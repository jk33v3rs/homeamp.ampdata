"""
Config Hierarchy Resolver

Resolves configuration values through 7-level scope hierarchy:
GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER

Each level can override values from higher levels.
Supports variable substitution and inheritance.
"""

import logging
import re
from typing import Any, Optional, Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ScopeLevel(Enum):
    """Scope hierarchy levels in order of precedence (lowest to highest)"""
    GLOBAL = 1
    SERVER = 2
    META_TAG = 3
    INSTANCE = 4
    WORLD = 5
    RANK = 6
    PLAYER = 7


class HierarchyResolver:
    """
    Resolve config values through multi-level scope hierarchy
    
    Resolution order (highest precedence wins):
    1. PLAYER (per-player overrides)
    2. RANK (LuckPerms rank-level config)
    3. WORLD (per-world config)
    4. INSTANCE (per-instance config)
    5. META_TAG (tag-based config groups)
    6. SERVER (per-server config)
    7. GLOBAL (default baseline)
    """
    
    def __init__(self, db_connection):
        """
        Initialize hierarchy resolver
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
    
    def resolve_config_value(self, plugin_id: str, config_key: str,
                            instance_id: int = None,
                            world_name: str = None,
                            rank_name: str = None,
                            player_uuid: str = None) -> Tuple[Any, str, List[Dict]]:
        """
        Resolve config value through 7-level cascade
        
        Args:
            plugin_id: Plugin identifier
            config_key: Config key to resolve
            instance_id: Instance ID (optional)
            world_name: World name (optional)
            rank_name: Rank name (optional)
            player_uuid: Player UUID (optional)
            
        Returns:
            Tuple of (resolved_value, source_scope, resolution_chain)
            - resolved_value: Final resolved value
            - source_scope: Where value came from ('GLOBAL', 'SERVER', etc.)
            - resolution_chain: List of dicts showing full resolution path
        """
        resolution_chain = []
        resolved_value = None
        source_scope = None
        
        # 1. Check GLOBAL scope
        global_value = self._get_global_config(plugin_id, config_key)
        if global_value is not None:
            resolved_value = global_value
            source_scope = 'GLOBAL'
            resolution_chain.append({
                'scope': 'GLOBAL',
                'value': global_value,
                'overridden': False
            })
        
        # 2. Check SERVER scope (if we have instance_id)
        if instance_id:
            server_name = self._get_server_for_instance(instance_id)
            if server_name:
                server_value = self._get_server_config(plugin_id, config_key, server_name)
                if server_value is not None:
                    if resolved_value is not None:
                        resolution_chain[-1]['overridden'] = True
                    resolved_value = server_value
                    source_scope = 'SERVER'
                    resolution_chain.append({
                        'scope': 'SERVER',
                        'server': server_name,
                        'value': server_value,
                        'overridden': False
                    })
        
        # 3. Check META_TAG scope
        if instance_id:
            meta_tags = self._get_instance_meta_tags(instance_id)
            for tag in meta_tags:
                tag_value = self._get_meta_tag_config(plugin_id, config_key, tag['tag_id'])
                if tag_value is not None:
                    if resolved_value is not None and resolution_chain:
                        resolution_chain[-1]['overridden'] = True
                    resolved_value = tag_value
                    source_scope = f'META_TAG:{tag["tag_name"]}'
                    resolution_chain.append({
                        'scope': 'META_TAG',
                        'tag': tag['tag_name'],
                        'value': tag_value,
                        'overridden': False
                    })
        
        # 4. Check INSTANCE scope
        if instance_id:
            instance_value = self._get_instance_config(plugin_id, config_key, instance_id)
            if instance_value is not None:
                if resolved_value is not None and resolution_chain:
                    resolution_chain[-1]['overridden'] = True
                resolved_value = instance_value
                source_scope = 'INSTANCE'
                resolution_chain.append({
                    'scope': 'INSTANCE',
                    'instance_id': instance_id,
                    'value': instance_value,
                    'overridden': False
                })
        
        # 5. Check WORLD scope
        if instance_id and world_name:
            world_value = self._get_world_config(plugin_id, config_key, instance_id, world_name)
            if world_value is not None:
                if resolved_value is not None and resolution_chain:
                    resolution_chain[-1]['overridden'] = True
                resolved_value = world_value
                source_scope = 'WORLD'
                resolution_chain.append({
                    'scope': 'WORLD',
                    'world': world_name,
                    'value': world_value,
                    'overridden': False
                })
        
        # 6. Check RANK scope
        if instance_id and rank_name:
            rank_value = self._get_rank_config(plugin_id, config_key, instance_id, rank_name)
            if rank_value is not None:
                if resolved_value is not None and resolution_chain:
                    resolution_chain[-1]['overridden'] = True
                resolved_value = rank_value
                source_scope = 'RANK'
                resolution_chain.append({
                    'scope': 'RANK',
                    'rank': rank_name,
                    'value': rank_value,
                    'overridden': False
                })
        
        # 7. Check PLAYER scope (highest precedence)
        if instance_id and player_uuid:
            player_value = self._get_player_config(plugin_id, config_key, instance_id, player_uuid)
            if player_value is not None:
                if resolved_value is not None and resolution_chain:
                    resolution_chain[-1]['overridden'] = True
                resolved_value = player_value
                source_scope = 'PLAYER'
                resolution_chain.append({
                    'scope': 'PLAYER',
                    'player_uuid': player_uuid,
                    'value': player_value,
                    'overridden': False
                })
        
        # Apply variable substitution
        if isinstance(resolved_value, str):
            resolved_value = self.apply_substitution_vars(resolved_value, instance_id, world_name, rank_name, player_uuid)
        
        return resolved_value, source_scope, resolution_chain
    
    def get_effective_value(self, plugin_id: str, config_key: str, instance_id: int,
                           world_name: str = None, rank_name: str = None,
                           player_uuid: str = None) -> Any:
        """
        Get final effective value for instance (simplified version)
        
        Args:
            plugin_id: Plugin identifier
            config_key: Config key
            instance_id: Instance ID
            world_name: World name (optional)
            rank_name: Rank name (optional)
            player_uuid: Player UUID (optional)
            
        Returns:
            Final resolved value
        """
        value, _, _ = self.resolve_config_value(
            plugin_id, config_key, instance_id, world_name, rank_name, player_uuid
        )
        return value
    
    def get_override_chain(self, plugin_id: str, config_key: str, instance_id: int,
                          world_name: str = None, rank_name: str = None,
                          player_uuid: str = None) -> List[Dict]:
        """
        Show full hierarchy chain showing where value comes from
        
        Args:
            plugin_id: Plugin identifier
            config_key: Config key
            instance_id: Instance ID
            world_name: World name (optional)
            rank_name: Rank name (optional)
            player_uuid: Player UUID (optional)
            
        Returns:
            List of resolution steps
        """
        _, _, chain = self.resolve_config_value(
            plugin_id, config_key, instance_id, world_name, rank_name, player_uuid
        )
        return chain
    
    def apply_substitution_vars(self, value: str, instance_id: int = None,
                               world_name: str = None, rank_name: str = None,
                               player_uuid: str = None) -> str:
        """
        Apply variable substitution to config values
        
        Supported variables:
        - {INSTANCE_ID} - Instance ID
        - {INSTANCE_NAME} - Instance name
        - {WORLD} - World name
        - {RANK} - Rank name
        - {PLAYER_UUID} - Player UUID
        - {PLAYER_NAME} - Player name
        - {SERVER} - Server name
        
        Args:
            value: String value with variables
            instance_id: Instance ID
            world_name: World name
            rank_name: Rank name
            player_uuid: Player UUID
            
        Returns:
            String with variables substituted
        """
        if not isinstance(value, str):
            return value
        
        # Get instance info
        if instance_id:
            instance_info = self.db.execute_query(
                "SELECT instance_name, server_name FROM instances WHERE instance_id = %s",
                (instance_id,),
                fetch=True
            )
            if instance_info:
                value = value.replace('{INSTANCE_ID}', str(instance_id))
                value = value.replace('{INSTANCE_NAME}', instance_info[0]['instance_name'])
                value = value.replace('{SERVER}', instance_info[0]['server_name'])
        
        # World substitution
        if world_name:
            value = value.replace('{WORLD}', world_name)
        
        # Rank substitution
        if rank_name:
            value = value.replace('{RANK}', rank_name)
        
        # Player substitution
        if player_uuid:
            value = value.replace('{PLAYER_UUID}', player_uuid)
            # Player name lookup would require external API (Mojang/player database)
        
        return value
    
    # ========================================================================
    # SCOPE-SPECIFIC RESOLUTION METHODS
    # ========================================================================
    
    def resolve_for_world(self, plugin_id: str, config_key: str,
                         instance_id: int, world_name: str) -> Any:
        """Get config value resolved up to WORLD scope"""
        return self.get_effective_value(plugin_id, config_key, instance_id, world_name=world_name)
    
    def resolve_for_rank(self, plugin_id: str, config_key: str,
                        instance_id: int, rank_name: str) -> Any:
        """Get config value resolved up to RANK scope"""
        return self.get_effective_value(plugin_id, config_key, instance_id, rank_name=rank_name)
    
    def resolve_for_player(self, plugin_id: str, config_key: str,
                          instance_id: int, player_uuid: str,
                          world_name: str = None, rank_name: str = None) -> Any:
        """Get config value resolved up to PLAYER scope (full resolution)"""
        return self.get_effective_value(
            plugin_id, config_key, instance_id,
            world_name=world_name, rank_name=rank_name, player_uuid=player_uuid
        )
    
    # ========================================================================
    # DATABASE QUERY METHODS (one per scope level)
    # ========================================================================
    
    def _get_global_config(self, plugin_id: str, config_key: str) -> Optional[Any]:
        """Get GLOBAL scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM config_rules
                WHERE plugin_id = %s AND config_key = %s AND scope_type = 'GLOBAL'
                LIMIT 1
            """, (plugin_id, config_key), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting global config: {e}")
            return None
    
    def _get_server_config(self, plugin_id: str, config_key: str, server_name: str) -> Optional[Any]:
        """Get SERVER scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM config_rules
                WHERE plugin_id = %s AND config_key = %s 
                  AND scope_type = 'SERVER' AND server_name = %s
                LIMIT 1
            """, (plugin_id, config_key, server_name), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting server config: {e}")
            return None
    
    def _get_meta_tag_config(self, plugin_id: str, config_key: str, tag_id: int) -> Optional[Any]:
        """Get META_TAG scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM config_rules
                WHERE plugin_id = %s AND config_key = %s 
                  AND scope_type = 'META_TAG' AND meta_tag_id = %s
                LIMIT 1
            """, (plugin_id, config_key, tag_id), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting meta tag config: {e}")
            return None
    
    def _get_instance_config(self, plugin_id: str, config_key: str, instance_id: int) -> Optional[Any]:
        """Get INSTANCE scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM config_rules
                WHERE plugin_id = %s AND config_key = %s 
                  AND scope_type = 'INSTANCE' AND instance_id = %s
                LIMIT 1
            """, (plugin_id, config_key, instance_id), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting instance config: {e}")
            return None
    
    def _get_world_config(self, plugin_id: str, config_key: str,
                         instance_id: int, world_name: str) -> Optional[Any]:
        """Get WORLD scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM world_config_rules
                WHERE plugin_id = %s AND config_key = %s 
                  AND instance_id = %s AND world_name = %s
                LIMIT 1
            """, (plugin_id, config_key, instance_id, world_name), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting world config: {e}")
            return None
    
    def _get_rank_config(self, plugin_id: str, config_key: str,
                        instance_id: int, rank_name: str) -> Optional[Any]:
        """Get RANK scope config"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM rank_config_rules
                WHERE plugin_id = %s AND config_key = %s 
                  AND instance_id = %s AND rank_name = %s
                LIMIT 1
            """, (plugin_id, config_key, instance_id, rank_name), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting rank config: {e}")
            return None
    
    def _get_player_config(self, plugin_id: str, config_key: str,
                          instance_id: int, player_uuid: str) -> Optional[Any]:
        """Get PLAYER scope config (highest precedence)"""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM player_config_overrides
                WHERE plugin_id = %s AND config_key = %s 
                  AND instance_id = %s AND player_uuid = %s
                LIMIT 1
            """, (plugin_id, config_key, instance_id, player_uuid), fetch=True)
            
            return result[0]['config_value'] if result else None
        except Exception as e:
            logger.error(f"Error getting player config: {e}")
            return None
    
    def _get_server_for_instance(self, instance_id: int) -> Optional[str]:
        """Get server name for instance"""
        try:
            result = self.db.execute_query("""
                SELECT server_name FROM instances WHERE instance_id = %s
            """, (instance_id,), fetch=True)
            
            return result[0]['server_name'] if result else None
        except Exception as e:
            logger.error(f"Error getting server for instance: {e}")
            return None
    
    def _get_instance_meta_tags(self, instance_id: int) -> List[Dict]:
        """Get all meta tags assigned to instance"""
        try:
            result = self.db.execute_query("""
                SELECT mt.tag_id, mt.tag_name
                FROM instance_meta_tags imt
                JOIN meta_tags mt ON imt.tag_id = mt.tag_id
                WHERE imt.instance_id = %s
            """, (instance_id,), fetch=True)
            
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting instance meta tags: {e}")
            return []


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Mock database connection would go here
    # resolver = HierarchyResolver(db_connection)
    
    print("Hierarchy Resolver ready for integration")
