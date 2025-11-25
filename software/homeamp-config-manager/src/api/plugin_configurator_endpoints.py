"""
Plugin Configurator API Endpoints
Phase 2 implementation - Plugin configuration management with YAML editing
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import mysql.connector
import yaml
import json
import os

# Database connection helper
from .db_config import get_db_connection as get_db

router = APIRouter(prefix="/api/plugin-configurator", tags=["plugin-configurator"])

# ====================
# Pydantic Models
# ====================


class PluginListItem(BaseModel):
    """Plugin list item for selector"""

    plugin_id: int
    plugin_name: str
    friendly_name: Optional[str]
    category: Optional[str]
    total_instances: int
    has_baseline: bool
    has_variances: bool
    update_available: bool


class MetaTag(BaseModel):
    """Meta tag for plugin categorization"""

    tag_id: int
    tag_name: str
    tag_type: str
    color: Optional[str]


class PluginInstance(BaseModel):
    """Plugin instance for deployment targeting"""

    instance_id: int
    instance_name: str
    server_name: str
    instance_short: str
    has_plugin: bool


class PluginDetails(BaseModel):
    """Detailed plugin information"""

    plugin_id: int
    plugin_name: str
    friendly_name: Optional[str]
    category: Optional[str]
    description: Optional[str]
    baseline_exists: bool
    baseline_path: Optional[str]
    total_instances: int
    variance_count: int
    meta_tags: List[MetaTag]


class ConfigYamlResponse(BaseModel):
    """YAML configuration content"""

    plugin_id: int
    plugin_name: str
    instance_id: Optional[int]
    instance_name: Optional[str]
    yaml_content: str
    is_baseline: bool
    last_modified: Optional[datetime]


class VarianceItem(BaseModel):
    """Configuration variance entry"""

    variance_id: int
    instance_id: int
    instance_name: str
    server_name: str
    config_key: str
    expected_value: Any
    actual_value: Any
    is_intentional: bool
    reason: Optional[str]


class SaveConfigRequest(BaseModel):
    """Request to save config changes"""

    plugin_id: int
    instance_id: Optional[int]  # None = baseline
    yaml_content: str
    commit_message: Optional[str]


class DeployConfigRequest(BaseModel):
    """Request to deploy config to instances"""

    plugin_id: int
    target_instances: List[int]
    yaml_content: str
    deployment_notes: Optional[str]


class TagAssignmentRequest(BaseModel):
    """Assign/remove tags to plugin"""

    plugin_id: int
    tag_ids: List[int]


class MarkVarianceRequest(BaseModel):
    """Mark variance as intentional/unintentional"""

    variance_id: int
    is_intentional: bool
    reason: Optional[str]


# ====================
# Database Helper
# ====================


def get_db_connection():
    """Get MySQL database connection"""
    return get_db()


# ====================
# Endpoints
# ====================


@router.get("/plugins", response_model=List[PluginListItem])
async def list_plugins(
    search: Optional[str] = Query(None, description="Search plugin name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    has_variances: Optional[bool] = Query(None, description="Filter plugins with variances"),
):
    """
    List all plugins for selection
    Supports search, category filter, variance filter
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                p.plugin_id,
                p.plugin_name,
                p.friendly_name,
                p.category,
                COUNT(DISTINCT pi.instance_id) as total_instances,
                (p.baseline_config_path IS NOT NULL) as has_baseline,
                (SELECT COUNT(*) FROM config_variance_detected cv 
                 WHERE cv.plugin_id = p.plugin_id AND cv.is_intentional = FALSE) > 0 as has_variances,
                (SELECT COUNT(*) FROM plugin_versions pv 
                 WHERE pv.plugin_id = p.plugin_id AND pv.update_available = TRUE) > 0 as update_available
            FROM plugins p
            LEFT JOIN plugin_instances pi ON p.plugin_id = pi.plugin_id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (p.plugin_name LIKE %s OR p.friendly_name LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if category:
            query += " AND p.category = %s"
            params.append(category)

        query += " GROUP BY p.plugin_id ORDER BY p.plugin_name"

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Convert to Pydantic models
        plugins = []
        for row in results:
            if has_variances is not None and row["has_variances"] != has_variances:
                continue
            plugins.append(PluginListItem(**row))

        return plugins

    finally:
        cursor.close()
        conn.close()


@router.get("/plugins/{plugin_id}", response_model=PluginDetails)
async def get_plugin_details(plugin_id: int):
    """
    Get detailed plugin information including meta tags
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get plugin details
        cursor.execute(
            """
            SELECT 
                p.plugin_id,
                p.plugin_name,
                p.friendly_name,
                p.category,
                p.description,
                (p.baseline_config_path IS NOT NULL) as baseline_exists,
                p.baseline_config_path,
                COUNT(DISTINCT pi.instance_id) as total_instances,
                (SELECT COUNT(*) FROM config_variance_detected cv 
                 WHERE cv.plugin_id = p.plugin_id AND cv.is_intentional = FALSE) as variance_count
            FROM plugins p
            LEFT JOIN plugin_instances pi ON p.plugin_id = pi.plugin_id
            WHERE p.plugin_id = %s
            GROUP BY p.plugin_id
        """,
            (plugin_id,),
        )

        plugin = cursor.fetchone()
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")

        # Get meta tags
        cursor.execute(
            """
            SELECT mt.tag_id, mt.tag_name, mt.tag_type, mt.color
            FROM meta_tags mt
            INNER JOIN plugin_meta_tags pmt ON mt.tag_id = pmt.tag_id
            WHERE pmt.plugin_id = %s
        """,
            (plugin_id,),
        )

        tags = [MetaTag(**row) for row in cursor.fetchall()]
        plugin["meta_tags"] = tags

        return PluginDetails(**plugin)

    finally:
        cursor.close()
        conn.close()


@router.get("/plugins/{plugin_id}/config", response_model=ConfigYamlResponse)
async def get_plugin_config(
    plugin_id: int, instance_id: Optional[int] = Query(None, description="Instance ID (None = baseline)")
):
    """
    Get YAML configuration for plugin
    If instance_id is None, returns baseline config
    Otherwise returns instance-specific config
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get plugin info
        cursor.execute("SELECT plugin_name, baseline_config_path FROM plugins WHERE plugin_id = %s", (plugin_id,))
        plugin = cursor.fetchone()
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")

        if instance_id is None:
            # Return baseline config
            baseline_path = plugin["baseline_config_path"]
            if not baseline_path:
                raise HTTPException(status_code=404, detail="Baseline config not found")

            # Read baseline config from file
            try:
                with open(baseline_path, "r", encoding="utf-8") as f:
                    yaml_content = f.read()
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Baseline file not found: {baseline_path}")

            return ConfigYamlResponse(
                plugin_id=plugin_id,
                plugin_name=plugin["plugin_name"],
                instance_id=None,
                instance_name=None,
                yaml_content=yaml_content,
                is_baseline=True,
                last_modified=None,
            )

        else:
            # Return instance-specific config
            cursor.execute(
                """
                SELECT i.instance_name, pi.config_path, pi.config_hash, pi.last_scanned
                FROM plugin_instances pi
                INNER JOIN instances i ON pi.instance_id = i.instance_id
                WHERE pi.plugin_id = %s AND pi.instance_id = %s
            """,
                (plugin_id, instance_id),
            )

            instance = cursor.fetchone()
            if not instance:
                raise HTTPException(status_code=404, detail="Plugin instance not found")

            # Read instance config from file
            config_path = instance["config_path"]
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    yaml_content = f.read()
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Config file not found: {config_path}")

            return ConfigYamlResponse(
                plugin_id=plugin_id,
                plugin_name=plugin["plugin_name"],
                instance_id=instance_id,
                instance_name=instance["instance_name"],
                yaml_content=yaml_content,
                is_baseline=False,
                last_modified=instance["last_scanned"],
            )

    finally:
        cursor.close()
        conn.close()


@router.get("/plugins/{plugin_id}/instances", response_model=List[PluginInstance])
async def get_plugin_instances(plugin_id: int):
    """
    Get all instances where plugin is installed
    Used for deployment targeting
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                i.instance_id,
                i.instance_name,
                i.server_name,
                SUBSTRING_INDEX(i.instance_name, '-', 1) as instance_short,
                (pi.plugin_id IS NOT NULL) as has_plugin
            FROM instances i
            LEFT JOIN plugin_instances pi ON i.instance_id = pi.instance_id AND pi.plugin_id = %s
            ORDER BY i.server_name, i.instance_name
        """,
            (plugin_id,),
        )

        results = cursor.fetchall()
        return [PluginInstance(**row) for row in results]

    finally:
        cursor.close()
        conn.close()


@router.get("/plugins/{plugin_id}/variances", response_model=List[VarianceItem])
async def get_plugin_variances(
    plugin_id: int, intentional_only: Optional[bool] = Query(None, description="Filter intentional variances")
):
    """
    Get all configuration variances for a plugin
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                cv.variance_id,
                cv.instance_id,
                i.instance_name,
                i.server_name,
                cv.config_key,
                cv.expected_value,
                cv.actual_value,
                cv.is_intentional,
                cv.reason
            FROM config_variance_detected cv
            INNER JOIN instances i ON cv.instance_id = i.instance_id
            WHERE cv.plugin_id = %s
        """
        params = [plugin_id]

        if intentional_only is not None:
            query += " AND cv.is_intentional = %s"
            params.append(intentional_only)

        query += " ORDER BY i.instance_name, cv.config_key"

        cursor.execute(query, params)
        results = cursor.fetchall()

        return [VarianceItem(**row) for row in results]

    finally:
        cursor.close()
        conn.close()


@router.post("/plugins/{plugin_id}/save")
async def save_plugin_config(request: SaveConfigRequest):
    """
    Save YAML config changes (baseline or instance-specific)
    Creates deployment queue entry if not baseline
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Validate YAML syntax
        try:
            yaml.safe_load(request.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        if request.instance_id is None:
            # Update baseline config
            cursor.execute("SELECT baseline_config_path FROM plugins WHERE plugin_id = %s", (request.plugin_id,))
            result = cursor.fetchone()
            if not result or not result[0]:
                raise HTTPException(status_code=404, detail="Baseline config not found")

            baseline_path = result[0]
            with open(baseline_path, "w", encoding="utf-8") as f:
                f.write(request.yaml_content)

            # Log audit
            cursor.execute(
                """
                INSERT INTO audit_log (timestamp, user, action, description)
                VALUES (NOW(), %s, 'config_update', %s)
            """,
                ("system", f"Updated baseline config for plugin {request.plugin_id}"),
            )

        else:
            # Create deployment queue entry for instance
            cursor.execute(
                """
                INSERT INTO deployment_queue 
                (instance_id, plugin_id, config_content, status, created_at, deployment_notes)
                VALUES (%s, %s, %s, 'pending', NOW(), %s)
            """,
                (request.instance_id, request.plugin_id, request.yaml_content, request.commit_message),
            )

            # Log audit
            cursor.execute(
                """
                INSERT INTO audit_log (timestamp, user, action, description)
                VALUES (NOW(), %s, 'deployment_queued', %s)
            """,
                ("system", f"Queued deployment for plugin {request.plugin_id} to instance {request.instance_id}"),
            )

        conn.commit()
        return {"status": "success", "message": "Configuration saved"}

    finally:
        cursor.close()
        conn.close()


@router.post("/plugins/{plugin_id}/deploy")
async def deploy_plugin_config(request: DeployConfigRequest):
    """
    Deploy config to multiple instances
    Creates deployment queue entries for all target instances
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Validate YAML syntax
        try:
            yaml.safe_load(request.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Create deployment queue entries
        for instance_id in request.target_instances:
            cursor.execute(
                """
                INSERT INTO deployment_queue 
                (instance_id, plugin_id, config_content, status, created_at, deployment_notes)
                VALUES (%s, %s, %s, 'pending', NOW(), %s)
            """,
                (instance_id, request.plugin_id, request.yaml_content, request.deployment_notes),
            )

        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (timestamp, user, action, description)
            VALUES (NOW(), %s, 'bulk_deployment', %s)
        """,
            (
                "system",
                f"Queued deployment for plugin {request.plugin_id} to {len(request.target_instances)} instances",
            ),
        )

        conn.commit()
        return {
            "status": "success",
            "message": f"Deployment queued for {len(request.target_instances)} instances",
            "target_count": len(request.target_instances),
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/plugins/{plugin_id}/tags")
async def assign_meta_tags(request: TagAssignmentRequest):
    """
    Assign meta tags to plugin
    Replaces existing tag assignments
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete existing tags
        cursor.execute("DELETE FROM plugin_meta_tags WHERE plugin_id = %s", (request.plugin_id,))

        # Insert new tags
        for tag_id in request.tag_ids:
            cursor.execute(
                """
                INSERT INTO plugin_meta_tags (plugin_id, tag_id, assigned_at)
                VALUES (%s, %s, NOW())
            """,
                (request.plugin_id, tag_id),
            )

        conn.commit()
        return {"status": "success", "message": f"Assigned {len(request.tag_ids)} tags"}

    finally:
        cursor.close()
        conn.close()


@router.post("/variances/mark")
async def mark_variance_intentional(request: MarkVarianceRequest):
    """
    Mark a variance as intentional or unintentional
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE config_variance_detected
            SET is_intentional = %s, reason = %s, last_updated = NOW()
            WHERE variance_id = %s
        """,
            (request.is_intentional, request.reason, request.variance_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Variance not found")

        conn.commit()
        return {"status": "success", "message": "Variance status updated"}

    finally:
        cursor.close()
        conn.close()


@router.get("/meta-tags", response_model=List[MetaTag])
async def list_meta_tags(tag_type: Optional[str] = Query(None, description="Filter by tag type")):
    """
    List all available meta tags
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = "SELECT tag_id, tag_name, tag_type, color FROM meta_tags WHERE 1=1"
        params = []

        if tag_type:
            query += " AND tag_type = %s"
            params.append(tag_type)

        query += " ORDER BY tag_type, tag_name"

        cursor.execute(query, params)
        results = cursor.fetchall()

        return [MetaTag(**row) for row in results]

    finally:
        cursor.close()
        conn.close()
