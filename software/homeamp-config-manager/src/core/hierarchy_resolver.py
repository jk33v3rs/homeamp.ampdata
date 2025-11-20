"""
Config Hierarchy Resolver

Implements the 7-level config hierarchy resolution cascade:
GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER

Resolves config values based on scope priority, with more specific scopes
overriding more general ones.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ScopeLevel(Enum):
    """Config scope levels in priority order (lowest to highest)"""
    GLOBAL = 0
    SERVER = 1
    META_TAG = 2
    INSTANCE = 3
    WORLD = 4
    RANK = 5
    PLAYER = 6


@dataclass
class ConfigContext:
    """Context for config resolution"""
    plugin_id: str
    config_file: str
    config_key: str
    
    # Scope identifiers (provide what's relevant)
    server_name: Optional[str] = None
    meta_tag_ids: Optional[List[int]] = None  # Instance can have multiple tags
    instance_id: Optional[str] = None
    world_name: Optional[str] = None
    rank_name: Optional[str] = None
    player_uuid: Optional[str] = None


@dataclass
class ResolvedConfig:
    """Resolved config value with metadata"""
    value: Any
    value_type: str
    scope_level: str
    rule_id: int
    priority: int
    notes: Optional[str] = None


class ConfigHierarchyResolver:
    """Resolve config values through hierarchy cascade"""
    
    def __init__(self, db_connection):
        """
        Initialize resolver with database connection.
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
    
    def resolve_config(self, context: ConfigContext) -> Optional[ResolvedConfig]:
        """
        Resolve a config value for given context.
        
        Resolution order (most specific wins):
        1. PLAYER (if player_uuid provided)
        2. RANK (if rank_name provided)
        3. WORLD (if world_name provided)
        4. INSTANCE (if instance_id provided)
        5. META_TAG (if meta_tag_ids provided)
        6. SERVER (if server_name provided)
        7. GLOBAL (always checked)
        
        Args:
            context: ConfigContext with scope identifiers
            
        Returns:
            ResolvedConfig object or None if no rule found
        """
        # Query all matching rules across all scope levels
        rules = self._query_matching_rules(context)
        
        if not rules:
            logger.debug(f"No rules found for {context.plugin_id}/{context.config_file}/{context.config_key}")
            return None
        
        # Find highest priority rule
        best_rule = self._select_best_rule(rules, context)
        
        if best_rule:
            logger.debug(
                f"Resolved {context.config_key} = {best_rule['value']} "
                f"(scope: {best_rule['scope_level']}, priority: {best_rule['priority']})"
            )
            
            return ResolvedConfig(
                value=json.loads(best_rule['config_value']),
                value_type=best_rule['value_type'],
                scope_level=best_rule['scope_level'],
                rule_id=best_rule['rule_id'],
                priority=best_rule['priority'],
                notes=best_rule['notes']
            )
        
        return None
    
    def _query_matching_rules(self, context: ConfigContext) -> List[Dict[str, Any]]:
        """
        Query all config rules matching the context.
        
        Args:
            context: ConfigContext
            
        Returns:
            List of matching rule dicts
        """
        cursor = self.db.cursor(dictionary=True)
        
        # Build dynamic query based on provided context
        conditions = [
            "plugin_id = %s",
            "config_file = %s",
            "config_key = %s",
            "is_active = TRUE"
        ]
        params = [context.plugin_id, context.config_file, context.config_key]
        
        # Add scope-specific conditions using OR (any matching scope)
        scope_conditions = []
        
        # GLOBAL (always matches)
        scope_conditions.append("scope_level = 'GLOBAL'")
        
        # SERVER
        if context.server_name:
            scope_conditions.append("(scope_level = 'SERVER' AND server_name = %s)")
            params.append(context.server_name)
        
        # META_TAG
        if context.meta_tag_ids:
            placeholders = ', '.join(['%s'] * len(context.meta_tag_ids))
            scope_conditions.append(f"(scope_level = 'META_TAG' AND meta_tag_id IN ({placeholders}))")
            params.extend(context.meta_tag_ids)
        
        # INSTANCE
        if context.instance_id:
            scope_conditions.append("(scope_level = 'INSTANCE' AND instance_id = %s)")
            params.append(context.instance_id)
        
        # WORLD
        if context.world_name and context.instance_id:
            scope_conditions.append(
                "(scope_level = 'WORLD' AND instance_id = %s AND world_name = %s)"
            )
            params.extend([context.instance_id, context.world_name])
        
        # RANK
        if context.rank_name and context.instance_id:
            scope_conditions.append(
                "(scope_level = 'RANK' AND instance_id = %s AND rank_name = %s)"
            )
            params.extend([context.instance_id, context.rank_name])
        
        # PLAYER
        if context.player_uuid and context.instance_id:
            scope_conditions.append(
                "(scope_level = 'PLAYER' AND instance_id = %s AND player_uuid = %s)"
            )
            params.extend([context.instance_id, context.player_uuid])
        
        # Combine all conditions
        scope_clause = " OR ".join(scope_conditions)
        conditions.append(f"({scope_clause})")
        
        query = f"""
        SELECT 
            rule_id, scope_level, server_name, meta_tag_id, instance_id,
            world_name, rank_name, player_uuid,
            plugin_id, config_file, config_key, config_value, value_type,
            priority, notes, created_at
        FROM config_rules
        WHERE {' AND '.join(conditions)}
        ORDER BY priority DESC, created_at DESC
        """
        
        cursor.execute(query, params)
        rules = cursor.fetchall()
        
        logger.debug(f"Found {len(rules)} matching rules for {context.config_key}")
        return rules
    
    def _select_best_rule(
        self, 
        rules: List[Dict[str, Any]], 
        context: ConfigContext
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best rule based on scope hierarchy and priority.
        
        Scope hierarchy (most specific to least specific):
        PLAYER > RANK > WORLD > INSTANCE > META_TAG > SERVER > GLOBAL
        
        Within same scope level, higher priority wins.
        
        Args:
            rules: List of matching rules
            context: ConfigContext
            
        Returns:
            Best matching rule dict or None
        """
        if not rules:
            return None
        
        # Score each rule based on scope level
        scored_rules = []
        
        for rule in rules:
            scope_score = self._calculate_scope_score(rule, context)
            scored_rules.append((scope_score, rule['priority'], rule))
        
        # Sort by scope score (desc), then priority (desc)
        scored_rules.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        best_rule = scored_rules[0][2]
        
        if len(scored_rules) > 1:
            logger.debug(
                f"Selected rule at {best_rule['scope_level']} scope "
                f"over {len(scored_rules) - 1} other(s)"
            )
        
        return best_rule
    
    def _calculate_scope_score(
        self, 
        rule: Dict[str, Any], 
        context: ConfigContext
    ) -> int:
        """
        Calculate score for a rule based on scope specificity.
        
        Args:
            rule: Rule dict
            context: ConfigContext
            
        Returns:
            Score (higher = more specific)
        """
        scope_level = rule['scope_level']
        
        # Base scores by scope level
        scope_scores = {
            'PLAYER': 600,
            'RANK': 500,
            'WORLD': 400,
            'INSTANCE': 300,
            'META_TAG': 200,
            'SERVER': 100,
            'GLOBAL': 0
        }
        
        score = scope_scores.get(scope_level, 0)
        
        # Bonus for META_TAG rules matching instance's primary tag
        if scope_level == 'META_TAG' and context.meta_tag_ids:
            # If rule matches first meta tag (primary), add bonus
            if rule['meta_tag_id'] == context.meta_tag_ids[0]:
                score += 50
        
        return score
    
    def resolve_all_configs(
        self, 
        context: ConfigContext,
        config_keys: Optional[List[str]] = None
    ) -> Dict[str, ResolvedConfig]:
        """
        Resolve multiple config keys at once.
        
        Args:
            context: ConfigContext (without config_key set)
            config_keys: List of config keys to resolve (None = all keys for plugin/file)
            
        Returns:
            Dict mapping config_key to ResolvedConfig
        """
        resolved = {}
        
        if config_keys:
            # Resolve specific keys
            for key in config_keys:
                ctx = ConfigContext(
                    plugin_id=context.plugin_id,
                    config_file=context.config_file,
                    config_key=key,
                    server_name=context.server_name,
                    meta_tag_ids=context.meta_tag_ids,
                    instance_id=context.instance_id,
                    world_name=context.world_name,
                    rank_name=context.rank_name,
                    player_uuid=context.player_uuid
                )
                
                result = self.resolve_config(ctx)
                if result:
                    resolved[key] = result
        else:
            # Query all available keys for this plugin/file
            available_keys = self._get_available_keys(
                context.plugin_id, 
                context.config_file
            )
            
            for key in available_keys:
                ctx = ConfigContext(
                    plugin_id=context.plugin_id,
                    config_file=context.config_file,
                    config_key=key,
                    server_name=context.server_name,
                    meta_tag_ids=context.meta_tag_ids,
                    instance_id=context.instance_id,
                    world_name=context.world_name,
                    rank_name=context.rank_name,
                    player_uuid=context.player_uuid
                )
                
                result = self.resolve_config(ctx)
                if result:
                    resolved[key] = result
        
        return resolved
    
    def _get_available_keys(self, plugin_id: str, config_file: str) -> List[str]:
        """
        Get all config keys available for a plugin/file.
        
        Args:
            plugin_id: Plugin identifier
            config_file: Config filename
            
        Returns:
            List of config keys
        """
        cursor = self.db.cursor()
        
        query = """
        SELECT DISTINCT config_key
        FROM config_rules
        WHERE plugin_id = %s AND config_file = %s AND is_active = TRUE
        ORDER BY config_key
        """
        
        cursor.execute(query, (plugin_id, config_file))
        return [row[0] for row in cursor.fetchall()]
    
    def explain_resolution(self, context: ConfigContext) -> Dict[str, Any]:
        """
        Explain how a config value was resolved (for debugging).
        
        Args:
            context: ConfigContext
            
        Returns:
            Dict with resolution explanation
        """
        rules = self._query_matching_rules(context)
        best_rule = self._select_best_rule(rules, context) if rules else None
        
        # Calculate scores for all rules
        scored_rules = []
        for rule in rules:
            score = self._calculate_scope_score(rule, context)
            scored_rules.append({
                'scope': rule['scope_level'],
                'priority': rule['priority'],
                'score': score,
                'value': json.loads(rule['config_value']),
                'selected': rule == best_rule
            })
        
        scored_rules.sort(key=lambda x: (x['score'], x['priority']), reverse=True)
        
        return {
            'context': {
                'plugin': context.plugin_id,
                'file': context.config_file,
                'key': context.config_key,
                'server': context.server_name,
                'meta_tags': context.meta_tag_ids,
                'instance': context.instance_id,
                'world': context.world_name,
                'rank': context.rank_name,
                'player': context.player_uuid
            },
            'total_rules': len(rules),
            'evaluated_rules': scored_rules,
            'selected_value': json.loads(best_rule['config_value']) if best_rule else None,
            'selected_scope': best_rule['scope_level'] if best_rule else None
        }


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # Example: Resolve a config value
    # import mysql.connector
    # db = mysql.connector.connect(...)
    # 
    # resolver = ConfigHierarchyResolver(db)
    # 
    # # Resolve spawn-protection for a specific instance
    # context = ConfigContext(
    #     plugin_id='server.properties',
    #     config_file='server.properties',
    #     config_key='spawn-protection',
    #     server_name='hetzner',
    #     instance_id='BENT01'
    # )
    # 
    # result = resolver.resolve_config(context)
    # if result:
    #     print(f"spawn-protection = {result.value} (from {result.scope_level} scope)")
    # 
    # # Explain resolution
    # explanation = resolver.explain_resolution(context)
    # print("\nResolution explanation:")
    # for rule in explanation['evaluated_rules']:
    #     selected = "" if rule['selected'] else " "
    #     print(f"  {selected} {rule['scope']}: {rule['value']} (score: {rule['score']}, priority: {rule['priority']})")
    
    pass
