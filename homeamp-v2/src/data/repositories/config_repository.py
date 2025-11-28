"""HomeAMP V2.0 - Configuration repository."""

from typing import List, Optional

from homeamp_v2.data.models.config import ConfigRule, ConfigValue, ConfigVariance
from homeamp_v2.data.repositories.base_repository import BaseRepository
from sqlalchemy import and_, select


class ConfigRepository(BaseRepository[ConfigRule]):
    """Config repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(ConfigRule, session)

    def get_config_values(
        self, instance_id: int, plugin_name: Optional[str] = None
    ) -> List[ConfigValue]:
        """Get config values for an instance."""
        stmt = select(ConfigValue).where(ConfigValue.instance_id == instance_id)

        if plugin_name:
            stmt = stmt.where(ConfigValue.plugin_name == plugin_name)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_variances(
        self, instance_id: Optional[int] = None, severity: Optional[str] = None
    ) -> List[ConfigVariance]:
        """Get config variances."""
        stmt = select(ConfigVariance)

        if instance_id:
            stmt = stmt.where(ConfigVariance.instance_id == instance_id)

        if severity:
            stmt = stmt.where(ConfigVariance.severity == severity)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_rule_by_key(
        self, plugin_name: str, config_file: str, config_key: str
    ) -> Optional[ConfigRule]:
        """Get config rule by key path."""
        stmt = select(ConfigRule).where(
            and_(
                ConfigRule.plugin_name == plugin_name,
                ConfigRule.config_file == config_file,
                ConfigRule.config_key == config_key,
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_enforced_rules(self) -> List[ConfigRule]:
        """Get all enforced config rules."""
        stmt = select(ConfigRule).where(ConfigRule.enforcement == "enforced")
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_global_rules(self) -> List[ConfigRule]:
        """Get all global scope config rules.
        
        Returns:
            List of ConfigRule with scope_type='global'
        """
        stmt = select(ConfigRule).where(ConfigRule.scope_type == "global")
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_rules_by_scope(
        self, scope_type: str, scope_id: Optional[int] = None
    ) -> List[ConfigRule]:
        """Get config rules by scope type and optional scope ID.
        
        Args:
            scope_type: Scope type (global, instance, group, world, region, rank)
            scope_id: Optional scope ID (required for non-global scopes)
            
        Returns:
            List of matching ConfigRule objects
        """
        stmt = select(ConfigRule).where(ConfigRule.scope_type == scope_type)
        
        if scope_id is not None:
            stmt = stmt.where(ConfigRule.scope_id == scope_id)
        elif scope_type != "global":
            # Non-global scopes should have a scope_id
            stmt = stmt.where(ConfigRule.scope_id.isnot(None))
            
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_rules_for_instance(
        self, instance_id: int, plugin_name: Optional[str] = None
    ) -> List[ConfigRule]:
        """Get all applicable rules for an instance (global + instance-specific).
        
        Args:
            instance_id: Instance ID
            plugin_name: Optional plugin name filter
            
        Returns:
            List of ConfigRule objects ordered by scope (global first, then instance)
        """
        # Get global rules
        global_stmt = select(ConfigRule).where(ConfigRule.scope_type == "global")
        
        # Get instance-specific rules
        instance_stmt = select(ConfigRule).where(
            and_(
                ConfigRule.scope_type == "instance",
                ConfigRule.scope_id == instance_id,
            )
        )
        
        if plugin_name:
            global_stmt = global_stmt.where(ConfigRule.plugin_name == plugin_name)
            instance_stmt = instance_stmt.where(ConfigRule.plugin_name == plugin_name)
        
        # Execute both queries
        global_result = self.session.execute(global_stmt)
        instance_result = self.session.execute(instance_stmt)
        
        # Combine results (global first, then instance-specific)
        rules = list(global_result.scalars().all()) + list(instance_result.scalars().all())
        return rules
