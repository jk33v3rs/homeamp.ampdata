"""
Config Management API Endpoints

New endpoints for config file management, hierarchy resolution,
meta-tags, worlds, ranks, and feature flags.

Import and register these in main api.py
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

# Import utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from engine.hierarchy_resolver import HierarchyResolver
from agent.config_modifier import ConfigModifier

# Create router
router = APIRouter(prefix="/api", tags=["config"])


# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# ============================================================================

class ConfigFileUpdate(BaseModel):
    """Request body for config file updates"""
    key_path: str
    value: Any
    validate: bool = True


class ConfigRuleCreate(BaseModel):
    """Request body for creating config rules"""
    plugin_id: str
    config_key: str
    config_value: Any
    scope_type: str  # GLOBAL, SERVER, META_TAG, INSTANCE
    server_name: Optional[str] = None
    meta_tag_id: Optional[int] = None
    instance_id: Optional[int] = None
    description: Optional[str] = None


class ConfigRuleUpdate(BaseModel):
    """Request body for updating config rules"""
    config_value: Optional[Any] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MetaTagCreate(BaseModel):
    """Request body for creating meta tags"""
    tag_name: str
    tag_description: Optional[str] = None
    category_id: Optional[int] = None


class MetaTagUpdate(BaseModel):
    """Request body for updating meta tags"""
    tag_name: Optional[str] = None
    tag_description: Optional[str] = None
    category_id: Optional[int] = None


class WorldRegister(BaseModel):
    """Request body for registering worlds"""
    instance_id: int
    world_name: str
    world_type: str  # normal, nether, end, custom
    world_seed: Optional[str] = None


class RankRegister(BaseModel):
    """Request body for registering ranks"""
    instance_id: int
    rank_name: str
    rank_priority: int
    rank_description: Optional[str] = None


class FeatureToggle(BaseModel):
    """Request body for toggling features"""
    is_enabled: bool


# ============================================================================
# CONFIG FILE ENDPOINTS
# ============================================================================

@router.get("/config/files")
async def list_config_files(
    instance_id: Optional[int] = None,
    plugin_id: Optional[str] = None,
    file_type: Optional[str] = None
):
    """
    List all config files tracked in the system
    
    Query params:
    - instance_id: Filter by instance
    - plugin_id: Filter by plugin
    - file_type: Filter by file type (yaml, json, properties, etc.)
    """
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        query = """
            SELECT ecf.config_file_id, ecf.instance_id, ecf.plugin_id,
                   ecf.file_path, ecf.file_type, ecf.current_hash, ecf.file_size,
                   ecf.last_modified_at, ecf.created_at,
                   i.instance_name, p.plugin_name
            FROM endpoint_config_files ecf
            JOIN instances i ON ecf.instance_id = i.instance_id
            LEFT JOIN plugins p ON ecf.plugin_id = p.plugin_id
            WHERE 1=1
        """
        params = []
        
        if instance_id:
            query += " AND ecf.instance_id = %s"
            params.append(instance_id)
        
        if plugin_id:
            query += " AND ecf.plugin_id = %s"
            params.append(plugin_id)
        
        if file_type:
            query += " AND ecf.file_type = %s"
            params.append(file_type)
        
        query += " ORDER BY i.instance_name, p.plugin_name, ecf.file_path"
        
        result = db.execute_query(query, tuple(params), fetch=True)
        
        return {
            "config_files": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.get("/config/files/{config_file_id}")
async def get_config_file_details(config_file_id: int):
    """Get detailed information about a specific config file"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        result = db.execute_query("""
            SELECT ecf.*, i.instance_name, i.folder_name, i.server_name,
                   p.plugin_name
            FROM endpoint_config_files ecf
            JOIN instances i ON ecf.instance_id = i.instance_id
            LEFT JOIN plugins p ON ecf.plugin_id = p.plugin_id
            WHERE ecf.config_file_id = %s
        """, (config_file_id,), fetch=True)
        
        if not result:
            raise HTTPException(status_code=404, detail="Config file not found")
        
        file_info = dict(result[0])
        
        # Get latest backup info
        backup = db.execute_query("""
            SELECT backup_id, backup_reason, backup_hash, created_at
            FROM endpoint_config_backups
            WHERE config_file_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (config_file_id,), fetch=True)
        
        file_info['latest_backup'] = dict(backup[0]) if backup else None
        
        return file_info
    finally:
        db.disconnect()


@router.get("/config/files/{config_file_id}/content")
async def get_config_file_content(config_file_id: int):
    """Get the actual content of a config file"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        # Get file path
        result = db.execute_query("""
            SELECT file_path, file_type FROM endpoint_config_files
            WHERE config_file_id = %s
        """, (config_file_id,), fetch=True)
        
        if not result:
            raise HTTPException(status_code=404, detail="Config file not found")
        
        file_path = result[0]['file_path']
        file_type = result[0]['file_type']
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "config_file_id": config_file_id,
                "file_path": file_path,
                "file_type": file_type,
                "content": content
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found on filesystem")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    finally:
        db.disconnect()


@router.put("/config/files/{config_file_id}/content")
async def update_config_file_content(
    config_file_id: int,
    update: ConfigFileUpdate
):
    """
    Update a specific key in a config file
    
    Uses safe modification with automatic backup and rollback
    """
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        # Get file info
        result = db.execute_query("""
            SELECT file_path, instance_id FROM endpoint_config_files
            WHERE config_file_id = %s
        """, (config_file_id,), fetch=True)
        
        if not result:
            raise HTTPException(status_code=404, detail="Config file not found")
        
        file_path = result[0]['file_path']
        instance_id = result[0]['instance_id']
        
        # Create backup first
        db.execute_query("""
            INSERT INTO endpoint_config_backups 
            (config_file_id, instance_id, backup_reason, backup_content, backup_hash)
            SELECT %s, %s, 'before_api_modification',
                   LOAD_FILE(%s),
                   SHA2(LOAD_FILE(%s), 256)
        """, (config_file_id, instance_id, file_path, file_path))
        
        # Modify config file
        modifier = ConfigModifier(db.conn)
        success, error = modifier.safe_modify(
            file_path,
            update.key_path,
            update.value,
            validate_after=update.validate
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Modification failed: {error}")
        
        # Log the change
        import json
        db.execute_query("""
            INSERT INTO endpoint_config_change_history
            (config_file_id, instance_id, change_type, changed_by, change_details)
            VALUES (%s, %s, 'modified', 'api', %s)
        """, (config_file_id, instance_id, json.dumps({
            'key_path': update.key_path,
            'new_value': update.value
        })))
        
        return {
            "success": True,
            "config_file_id": config_file_id,
            "modified_key": update.key_path,
            "new_value": update.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.disconnect()


@router.post("/config/files/{config_file_id}/backup")
async def create_config_backup(
    config_file_id: int,
    reason: str = "manual"
):
    """Create a manual backup of a config file"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        # Get file info
        result = db.execute_query("""
            SELECT file_path, instance_id FROM endpoint_config_files
            WHERE config_file_id = %s
        """, (config_file_id,), fetch=True)
        
        if not result:
            raise HTTPException(status_code=404, detail="Config file not found")
        
        file_path = result[0]['file_path']
        instance_id = result[0]['instance_id']
        
        # Create backup
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import hashlib
        backup_hash = hashlib.sha256(content.encode()).hexdigest()
        
        db.execute_query("""
            INSERT INTO endpoint_config_backups
            (config_file_id, instance_id, backup_reason, backup_content, backup_hash)
            VALUES (%s, %s, %s, %s, %s)
        """, (config_file_id, instance_id, reason, content, backup_hash))
        
        backup_id = db.cursor.lastrowid
        
        return {
            "backup_id": backup_id,
            "config_file_id": config_file_id,
            "reason": reason,
            "hash": backup_hash
        }
    finally:
        db.disconnect()


@router.get("/config/files/{config_file_id}/backups")
async def list_config_backups(
    config_file_id: int,
    limit: int = 10
):
    """List backup history for a config file"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        result = db.execute_query("""
            SELECT backup_id, config_file_id, backup_reason,
                   backup_hash, created_at,
                   LENGTH(backup_content) as backup_size
            FROM endpoint_config_backups
            WHERE config_file_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (config_file_id, limit), fetch=True)
        
        return {
            "config_file_id": config_file_id,
            "backups": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.post("/config/files/{config_file_id}/restore/{backup_id}")
async def restore_config_from_backup(
    config_file_id: int,
    backup_id: int
):
    """Restore a config file from a backup"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        # Get backup content
        result = db.execute_query("""
            SELECT backup_content, backup_hash, instance_id
            FROM endpoint_config_backups
            WHERE backup_id = %s AND config_file_id = %s
        """, (backup_id, config_file_id), fetch=True)
        
        if not result:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        backup_content = result[0]['backup_content']
        backup_hash = result[0]['backup_hash']
        instance_id = result[0]['instance_id']
        
        # Get file path
        file_result = db.execute_query("""
            SELECT file_path FROM endpoint_config_files
            WHERE config_file_id = %s
        """, (config_file_id,), fetch=True)
        
        file_path = file_result[0]['file_path']
        
        # Write backup content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        # Verify hash
        import hashlib
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        verify_hash = hashlib.sha256(content.encode()).hexdigest()
        
        if verify_hash != backup_hash:
            raise HTTPException(status_code=500, detail="Hash verification failed after restore")
        
        # Log the restore
        import json
        db.execute_query("""
            INSERT INTO endpoint_config_change_history
            (config_file_id, instance_id, change_type, changed_by, change_details, backup_id)
            VALUES (%s, %s, 'restored', 'api', %s, %s)
        """, (config_file_id, instance_id, json.dumps({
            'backup_id': backup_id,
            'backup_hash': backup_hash
        }), backup_id))
        
        return {
            "success": True,
            "config_file_id": config_file_id,
            "backup_id": backup_id,
            "restored_hash": verify_hash
        }
    finally:
        db.disconnect()


# ============================================================================
# HIERARCHY RESOLUTION ENDPOINTS
# ============================================================================

@router.get("/config/hierarchy")
async def query_hierarchy(
    plugin_id: str,
    config_key: str,
    instance_id: int,
    world_name: Optional[str] = None,
    rank_name: Optional[str] = None,
    player_uuid: Optional[str] = None
):
    """
    Query config hierarchy and show full resolution chain
    
    Returns the resolved value and the full cascade showing which
    levels were checked and which values were overridden.
    """
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        resolver = HierarchyResolver(db)
        
        value, source_scope, resolution_chain = resolver.resolve_config_value(
            plugin_id=plugin_id,
            config_key=config_key,
            instance_id=instance_id,
            world_name=world_name,
            rank_name=rank_name,
            player_uuid=player_uuid
        )
        
        return {
            "plugin_id": plugin_id,
            "config_key": config_key,
            "instance_id": instance_id,
            "resolved_value": value,
            "source_scope": source_scope,
            "resolution_chain": resolution_chain,
            "context": {
                "world": world_name,
                "rank": rank_name,
                "player": player_uuid
            }
        }
    finally:
        db.disconnect()


@router.get("/config/resolve")
async def resolve_config_value(
    plugin_id: str,
    config_key: str,
    instance_id: int,
    world_name: Optional[str] = None,
    rank_name: Optional[str] = None,
    player_uuid: Optional[str] = None
):
    """
    Resolve config value (simplified version - just returns the value)
    
    Use /config/hierarchy for full resolution chain details.
    """
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        resolver = HierarchyResolver(db)
        
        value = resolver.get_effective_value(
            plugin_id=plugin_id,
            config_key=config_key,
            instance_id=instance_id,
            world_name=world_name,
            rank_name=rank_name,
            player_uuid=player_uuid
        )
        
        return {
            "plugin_id": plugin_id,
            "config_key": config_key,
            "instance_id": instance_id,
            "value": value
        }
    finally:
        db.disconnect()


# ============================================================================
# CONFIG RULES ENDPOINTS
# ============================================================================

@router.post("/config/rules")
async def create_config_rule(rule: ConfigRuleCreate):
    """Create a new config rule at any scope level"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            INSERT INTO config_rules
            (plugin_id, config_key, config_value, scope_type,
             server_name, meta_tag_id, instance_id, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rule.plugin_id, rule.config_key, rule.config_value,
            rule.scope_type, rule.server_name, rule.meta_tag_id,
            rule.instance_id, rule.description
        ))
        
        rule_id = db.cursor.lastrowid
        
        return {
            "rule_id": rule_id,
            "created": True,
            **rule.dict()
        }
    finally:
        db.disconnect()


@router.put("/config/rules/{rule_id}")
async def update_config_rule(rule_id: int, update: ConfigRuleUpdate):
    """Update an existing config rule"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        # Build update query dynamically
        updates = []
        params = []
        
        if update.config_value is not None:
            updates.append("config_value = %s")
            params.append(update.config_value)
        
        if update.description is not None:
            updates.append("description = %s")
            params.append(update.description)
        
        if update.is_active is not None:
            updates.append("is_active = %s")
            params.append(update.is_active)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(rule_id)
        
        db.execute_query(f"""
            UPDATE config_rules
            SET {', '.join(updates)}
            WHERE rule_id = %s
        """, tuple(params))
        
        return {"rule_id": rule_id, "updated": True}
    finally:
        db.disconnect()


@router.delete("/config/rules/{rule_id}")
async def delete_config_rule(rule_id: int):
    """Delete a config rule"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            DELETE FROM config_rules WHERE rule_id = %s
        """, (rule_id,))
        
        return {"rule_id": rule_id, "deleted": True}
    finally:
        db.disconnect()


# ============================================================================
# VARIANCE ENDPOINTS
# ============================================================================

@router.get("/config/variance")
async def get_variance_report(
    plugin_id: Optional[str] = None,
    instance_id: Optional[int] = None,
    classification: Optional[str] = None
):
    """
    Get config variance report
    
    Classifications: NONE, VARIABLE, META_TAG, INSTANCE, DRIFT
    """
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        query = """
            SELECT * FROM v_config_variance_summary
            WHERE 1=1
        """
        params = []
        
        if plugin_id:
            query += " AND plugin_id = %s"
            params.append(plugin_id)
        
        if instance_id:
            query += " AND instance_id = %s"
            params.append(instance_id)
        
        if classification:
            query += " AND variance_classification = %s"
            params.append(classification)
        
        result = db.execute_query(query, tuple(params), fetch=True)
        
        return {
            "variance": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


# ============================================================================
# META TAG ENDPOINTS
# ============================================================================

@router.get("/meta-tags")
async def list_meta_tags():
    """List all meta tags"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        result = db.execute_query("""
            SELECT tag_id, tag_name, tag_description, created_at
            FROM meta_tags
            ORDER BY tag_name
        """, fetch=True)
        
        return {
            "tags": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.post("/meta-tags")
async def create_meta_tag(tag: MetaTagCreate):
    """Create a new meta tag"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            INSERT INTO meta_tags (tag_name, tag_description)
            VALUES (%s, %s)
        """, (tag.tag_name, tag.tag_description))
        
        tag_id = db.cursor.lastrowid
        
        return {
            "tag_id": tag_id,
            "created": True,
            **tag.dict()
        }
    finally:
        db.disconnect()


@router.put("/meta-tags/{tag_id}")
async def update_meta_tag(tag_id: int, update: MetaTagUpdate):
    """Update a meta tag"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        updates = []
        params = []
        
        if update.tag_name:
            updates.append("tag_name = %s")
            params.append(update.tag_name)
        
        if update.tag_description is not None:
            updates.append("tag_description = %s")
            params.append(update.tag_description)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(tag_id)
        
        db.execute_query(f"""
            UPDATE meta_tags
            SET {', '.join(updates)}
            WHERE tag_id = %s
        """, tuple(params))
        
        return {"tag_id": tag_id, "updated": True}
    finally:
        db.disconnect()


@router.delete("/meta-tags/{tag_id}")
async def delete_meta_tag(tag_id: int):
    """Delete a meta tag"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            DELETE FROM meta_tags WHERE tag_id = %s
        """, (tag_id,))
        
        return {"tag_id": tag_id, "deleted": True}
    finally:
        db.disconnect()


@router.post("/instances/{instance_id}/meta-tags")
async def assign_meta_tag(instance_id: int, tag_id: int = Body(...)):
    """Assign a meta tag to an instance"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            INSERT INTO instance_meta_tags (instance_id, tag_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE instance_id = instance_id
        """, (instance_id, tag_id))
        
        return {
            "instance_id": instance_id,
            "tag_id": tag_id,
            "assigned": True
        }
    finally:
        db.disconnect()


@router.delete("/instances/{instance_id}/meta-tags/{tag_id}")
async def remove_meta_tag(instance_id: int, tag_id: int):
    """Remove a meta tag from an instance"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            DELETE FROM instance_meta_tags
            WHERE instance_id = %s AND tag_id = %s
        """, (instance_id, tag_id))
        
        return {
            "instance_id": instance_id,
            "tag_id": tag_id,
            "removed": True
        }
    finally:
        db.disconnect()


# ============================================================================
# WORLD ENDPOINTS
# ============================================================================

@router.get("/worlds")
async def list_worlds(instance_id: Optional[int] = None):
    """List all worlds, optionally filtered by instance"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        query = """
            SELECT w.world_id, w.instance_id, w.world_name, w.world_type,
                   w.world_seed, w.discovered_at,
                   i.instance_name
            FROM worlds w
            JOIN instances i ON w.instance_id = i.instance_id
            WHERE 1=1
        """
        params = []
        
        if instance_id:
            query += " AND w.instance_id = %s"
            params.append(instance_id)
        
        query += " ORDER BY i.instance_name, w.world_name"
        
        result = db.execute_query(query, tuple(params), fetch=True)
        
        return {
            "worlds": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.post("/worlds")
async def register_world(world: WorldRegister):
    """Register a new world"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            INSERT INTO worlds (instance_id, world_name, world_type, world_seed)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE world_type = VALUES(world_type)
        """, (world.instance_id, world.world_name, world.world_type, world.world_seed))
        
        world_id = db.cursor.lastrowid
        
        return {
            "world_id": world_id,
            "created": True,
            **world.dict()
        }
    finally:
        db.disconnect()


# ============================================================================
# RANK ENDPOINTS
# ============================================================================

@router.get("/ranks")
async def list_ranks(instance_id: Optional[int] = None):
    """List all ranks, optionally filtered by instance"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        query = """
            SELECT r.rank_id, r.instance_id, r.rank_name, r.rank_priority,
                   r.rank_description, r.discovered_at,
                   i.instance_name
            FROM ranks r
            JOIN instances i ON r.instance_id = i.instance_id
            WHERE 1=1
        """
        params = []
        
        if instance_id:
            query += " AND r.instance_id = %s"
            params.append(instance_id)
        
        query += " ORDER BY i.instance_name, r.rank_priority DESC"
        
        result = db.execute_query(query, tuple(params), fetch=True)
        
        return {
            "ranks": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.post("/ranks")
async def register_rank(rank: RankRegister):
    """Register a new rank"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            INSERT INTO ranks (instance_id, rank_name, rank_priority, rank_description)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rank_priority = VALUES(rank_priority)
        """, (rank.instance_id, rank.rank_name, rank.rank_priority, rank.rank_description))
        
        rank_id = db.cursor.lastrowid
        
        return {
            "rank_id": rank_id,
            "created": True,
            **rank.dict()
        }
    finally:
        db.disconnect()


# ============================================================================
# FEATURE FLAG ENDPOINTS
# ============================================================================

@router.get("/features")
async def list_feature_flags():
    """List all feature flags"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        result = db.execute_query("""
            SELECT feature_id, feature_name, feature_description,
                   is_enabled, default_value, created_at, updated_at
            FROM feature_flags
            ORDER BY feature_name
        """, fetch=True)
        
        return {
            "features": [dict(row) for row in result],
            "count": len(result)
        }
    finally:
        db.disconnect()


@router.put("/features/{feature_id}")
async def toggle_feature_flag(feature_id: int, toggle: FeatureToggle):
    """Enable or disable a feature flag"""
    from ..database.db_access import ConfigDatabase
    db = ConfigDatabase()
    
    try:
        db.execute_query("""
            UPDATE feature_flags
            SET is_enabled = %s
            WHERE feature_id = %s
        """, (toggle.is_enabled, feature_id))
        
        return {
            "feature_id": feature_id,
            "is_enabled": toggle.is_enabled,
            "updated": True
        }
    finally:
        db.disconnect()


# ============================================================================
# EXPORT ROUTER
# ============================================================================

def get_config_router():
    """Export the router for inclusion in main API"""
    return router
