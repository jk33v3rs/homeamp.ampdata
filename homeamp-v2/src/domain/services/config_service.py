"""HomeAMP V2.0 - Configuration service for validation and variance detection."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from homeamp_v2.core.exceptions import ConfigNotFoundError, ValidationError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for configuration validation and variance detection."""

    def __init__(self, uow: UnitOfWork):
        """Initialize configuration service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def validate_config_value(self, instance_id: int, config_rule_id: int, value: str) -> bool:
        """Validate a config value against its rule.

        Args:
            instance_id: Instance ID
            config_rule_id: Config rule ID
            value: Value to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
            ConfigNotFoundError: If rule not found
        """
        rule = self.uow.configs.get_by_id(config_rule_id)
        if not rule:
            raise ConfigNotFoundError(f"Config rule {config_rule_id} not found")

        try:
            # Type validation
            if rule.value_type == "integer":
                int(value)
            elif rule.value_type == "float":
                float(value)
            elif rule.value_type == "boolean":
                if value.lower() not in ["true", "false"]:
                    raise ValidationError(f"Invalid boolean value: {value}")

            # Range validation for numeric types
            if rule.min_value is not None:
                num_value = float(value)
                if num_value < float(rule.min_value):
                    raise ValidationError(f"Value {value} below minimum {rule.min_value}")

            if rule.max_value is not None:
                num_value = float(value)
                if num_value > float(rule.max_value):
                    raise ValidationError(f"Value {value} above maximum {rule.max_value}")

            # Allowed values validation
            if rule.allowed_values:
                allowed = [v.strip() for v in rule.allowed_values.split(",")]
                if value not in allowed:
                    raise ValidationError(f"Value '{value}' not in allowed values: {allowed}")

            logger.debug(f"Config value validated: {rule.config_key}={value}")
            return True

        except ValueError as e:
            raise ValidationError(f"Invalid value type for {rule.config_key}: {e}") from e

    def detect_variances(self, instance_id: int) -> List[Dict]:
        """Detect configuration variances for an instance.

        Args:
            instance_id: Instance ID

        Returns:
            List of variances detected

        Raises:
            ConfigNotFoundError: If instance not found
        """
        instance = self.uow.instances.get_by_id(instance_id)
        if not instance:
            raise ConfigNotFoundError(f"Instance {instance_id} not found")

        logger.info(f"Detecting variances for instance: {instance.name}")

        variances = []
        config_values = self.uow.configs.get_config_values(instance_id)
        enforced_rules = self.uow.configs.get_enforced_rules()

        for rule in enforced_rules:
            # Find matching config value
            matching_value = None
            for value in config_values:
                if (
                    value.plugin_name == rule.plugin_name
                    and value.config_file == rule.config_file
                    and value.config_key == rule.config_key
                ):
                    matching_value = value
                    break

            if not matching_value:
                # Missing required config
                variances.append(
                    {
                        "type": "missing",
                        "plugin_name": rule.plugin_name,
                        "config_file": rule.config_file,
                        "config_key": rule.config_key,
                        "expected_value": rule.expected_value,
                        "actual_value": None,
                        "severity": "critical" if rule.enforcement == "enforced" else "warning",
                    }
                )
                continue

            # Check if value matches expected
            if rule.expected_value and matching_value.config_value != rule.expected_value:
                variances.append(
                    {
                        "type": "mismatch",
                        "plugin_name": rule.plugin_name,
                        "config_file": rule.config_file,
                        "config_key": rule.config_key,
                        "expected_value": rule.expected_value,
                        "actual_value": matching_value.config_value,
                        "severity": "critical" if rule.enforcement == "enforced" else "warning",
                    }
                )

        logger.info(f"Detected {len(variances)} variances for instance {instance.name}")
        return variances

    def enforce_config_rules(self, instance_id: int, dry_run: bool = True) -> Dict:
        """Enforce configuration rules on an instance.

        Args:
            instance_id: Instance ID
            dry_run: If True, only simulate changes

        Returns:
            Dictionary with enforcement results

        Raises:
            ConfigNotFoundError: If instance not found
        """
        instance = self.uow.instances.get_by_id(instance_id)
        if not instance:
            raise ConfigNotFoundError(f"Instance {instance_id} not found")

        logger.info(f"Enforcing config rules for instance: {instance.name} (dry_run={dry_run})")

        variances = self.detect_variances(instance_id)
        changes = []

        for variance in variances:
            if variance["severity"] == "critical":
                change = {
                    "plugin_name": variance["plugin_name"],
                    "config_file": variance["config_file"],
                    "config_key": variance["config_key"],
                    "old_value": variance["actual_value"],
                    "new_value": variance["expected_value"],
                    "action": "update" if variance["type"] == "mismatch" else "create",
                }

                if not dry_run:
                    # Implement actual config file modification
                    try:
                        config_file_path = Path(instance.base_path) / variance["config_file"]
                        if config_file_path.exists():
                            # Determine file format
                            file_format = "yaml" if config_file_path.suffix in [".yml", ".yaml"] else "json" if config_file_path.suffix == ".json" else "properties"
                            
                            # Load, modify, and save
                            config_data = self.parse_config_file(str(config_file_path), file_format)
                            
                            # Set nested key using dot notation
                            keys = variance["config_key"].split(".")
                            current = config_data
                            for key in keys[:-1]:
                                if key not in current:
                                    current[key] = {}
                                current = current[key]
                            current[keys[-1]] = variance["expected_value"]
                            
                            # Write back
                            if file_format == "yaml":
                                with open(config_file_path, "w", encoding="utf-8") as f:
                                    yaml.dump(config_data, f, default_flow_style=False)
                            elif file_format == "json":
                                import json
                                with open(config_file_path, "w", encoding="utf-8") as f:
                                    json.dump(config_data, f, indent=2)
                            elif file_format == "properties":
                                with open(config_file_path, "w", encoding="utf-8") as f:
                                    for key, value in config_data.items():
                                        f.write(f"{key}={value}\n")
                            
                            logger.info(f"Updated {variance['config_file']}: {variance['config_key']} = {variance['expected_value']}")
                        else:
                            logger.warning(f"Config file not found: {config_file_path}")
                    except Exception as e:
                        logger.error(f"Failed to modify config file: {e}")

                changes.append(change)

        result = {
            "instance_id": instance_id,
            "instance_name": instance.name,
            "dry_run": dry_run,
            "variances_found": len(variances),
            "changes_planned": len(changes),
            "changes": changes,
        }

        logger.info(
            f"Config enforcement complete: {len(variances)} variances, {len(changes)} changes planned"
        )
        return result

    def parse_config_file(self, file_path: str, file_format: str = "yaml") -> Dict:
        """Parse a configuration file.

        Args:
            file_path: Path to config file
            file_format: File format (yaml, json, properties)

        Returns:
            Parsed configuration dictionary

        Raises:
            ValidationError: If parsing fails
        """
        try:
            if file_format == "yaml":
                with open(file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            elif file_format == "json":
                import json

                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            elif file_format == "properties":
                config = {}
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                key, value = line.split("=", 1)
                                config[key.strip()] = value.strip()
                return config
            else:
                raise ValidationError(f"Unsupported config format: {file_format}")

        except Exception as e:
            raise ValidationError(f"Failed to parse config file {file_path}: {e}") from e

    def get_config_hierarchy(self, plugin_name: str) -> Dict:
        """Get configuration hierarchy for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Configuration hierarchy dictionary
        """
        # Get all rules for the plugin
        all_rules = self.uow.configs.get_all()
        plugin_rules = [r for r in all_rules if r.plugin_name == plugin_name]

        hierarchy = {"plugin_name": plugin_name, "files": {}}

        for rule in plugin_rules:
            if rule.config_file not in hierarchy["files"]:
                hierarchy["files"][rule.config_file] = {"keys": []}

            hierarchy["files"][rule.config_file]["keys"].append(
                {
                    "key": rule.config_key,
                    "expected_value": rule.expected_value,
                    "value_type": rule.value_type,
                    "enforcement": rule.enforcement,
                    "scope": rule.scope,
                }
            )

        return hierarchy

    def get_global_config_rules(self, plugin_name: Optional[str] = None) -> List[Dict]:
        """Get all global scope configuration rules.

        Args:
            plugin_name: Optional plugin name filter

        Returns:
            List of global config rules
        """
        global_rules = self.uow.configs.get_global_rules()

        if plugin_name:
            global_rules = [r for r in global_rules if r.plugin_name == plugin_name]

        logger.info(f"Retrieved {len(global_rules)} global config rules")
        return [
            {
                "id": rule.id,
                "plugin_name": rule.plugin_name,
                "file_path": rule.file_path,
                "key_path": rule.key_path,
                "expected_value": rule.expected_value,
                "enforcement_level": rule.enforcement_level,
                "description": rule.description,
            }
            for rule in global_rules
        ]

    def resolve_config_for_instance(
        self, instance_id: int, plugin_name: str, key_path: str
    ) -> Dict:
        """Resolve final config value for instance considering global and instance-specific rules.

        Args:
            instance_id: Instance ID
            plugin_name: Plugin name
            key_path: Config key path

        Returns:
            Resolution result with winning rule and value

        Raises:
            ConfigNotFoundError: If instance not found
        """
        instance = self.uow.instances.get_by_id(instance_id)
        if not instance:
            raise ConfigNotFoundError(f"Instance {instance_id} not found")

        # Get all applicable rules (global + instance-specific)
        rules = self.uow.configs.get_rules_for_instance(instance_id, plugin_name)

        # Filter by key_path
        matching_rules = [r for r in rules if r.key_path == key_path]

        if not matching_rules:
            logger.warning(
                f"No config rules found for {plugin_name}:{key_path} on instance {instance_id}"
            )
            return {
                "instance_id": instance_id,
                "plugin_name": plugin_name,
                "key_path": key_path,
                "resolved_value": None,
                "winning_rule": None,
                "rule_source": None,
            }

        # Instance-specific rules override global rules
        # Sort by scope_type: instance first, then global
        matching_rules.sort(key=lambda r: 0 if r.scope_type == "instance" else 1)

        winning_rule = matching_rules[0]

        logger.debug(
            f"Resolved {plugin_name}:{key_path} = {winning_rule.expected_value} "
            f"(scope: {winning_rule.scope_type})"
        )

        return {
            "instance_id": instance_id,
            "plugin_name": plugin_name,
            "key_path": key_path,
            "resolved_value": winning_rule.expected_value,
            "winning_rule": {
                "id": winning_rule.id,
                "scope_type": winning_rule.scope_type,
                "scope_id": winning_rule.scope_id,
                "enforcement_level": winning_rule.enforcement_level,
            },
            "rule_source": winning_rule.scope_type,
            "total_matching_rules": len(matching_rules),
        }

    def create_global_config_rule(
        self,
        plugin_name: str,
        file_path: str,
        key_path: str,
        expected_value: str,
        enforcement_level: str = "recommended",
        description: Optional[str] = None,
    ) -> Dict:
        """Create a new global configuration rule.

        Args:
            plugin_name: Plugin name
            file_path: Config file path
            key_path: Config key path (dot notation)
            expected_value: Expected value
            enforcement_level: Enforcement level (required, recommended, optional)
            description: Optional description

        Returns:
            Created rule details

        Raises:
            ValidationError: If enforcement level is invalid
        """
        from homeamp_v2.data.models.config import ConfigRule

        valid_levels = ["required", "recommended", "optional"]
        if enforcement_level not in valid_levels:
            raise ValidationError(
                f"Invalid enforcement level. Must be one of: {valid_levels}"
            )

        rule = ConfigRule(
            plugin_name=plugin_name,
            file_path=file_path,
            key_path=key_path,
            expected_value=expected_value,
            scope_type="global",
            scope_id=None,
            enforcement_level=enforcement_level,
            description=description,
        )

        self.uow.configs.add(rule)
        self.uow.commit()

        logger.info(
            f"Created global config rule: {plugin_name}:{file_path}:{key_path}"
        )

        return {
            "id": rule.id,
            "plugin_name": rule.plugin_name,
            "file_path": rule.file_path,
            "key_path": rule.key_path,
            "expected_value": rule.expected_value,
            "scope_type": rule.scope_type,
            "enforcement_level": rule.enforcement_level,
        }

