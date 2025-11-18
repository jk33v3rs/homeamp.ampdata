"""
Baseline Configuration Parser

Parses baseline markdown files and converts them into config_rules table entries.

Baseline files are expected to be in markdown format with structure:
    # Plugin Name
    ## config.yml
    ```yaml
    key: value
    nested:
      key: value
    ```
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedConfig:
    """Represents a parsed config entry from baseline"""
    plugin_id: str
    config_file: str
    config_key: str
    config_value: Any
    value_type: str
    scope_level: str = "GLOBAL"
    notes: Optional[str] = None


class BaselineParser:
    """Parse baseline markdown files into structured config rules"""
    
    def __init__(self):
        self.current_plugin: Optional[str] = None
        self.current_file: Optional[str] = None
        
    def parse_baseline_file(self, file_path: Path) -> List[ParsedConfig]:
        """
        Parse a baseline markdown file.
        
        Args:
            file_path: Path to the baseline markdown file
            
        Returns:
            List of ParsedConfig objects
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Baseline file not found: {file_path}")
            
        content = file_path.read_text(encoding='utf-8')
        return self.parse_baseline_content(content, file_path.stem)
    
    def parse_baseline_content(self, content: str, plugin_id: str) -> List[ParsedConfig]:
        """
        Parse baseline markdown content.
        
        Args:
            content: Markdown content
            plugin_id: Plugin identifier (from filename)
            
        Returns:
            List of ParsedConfig objects
        """
        configs = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for plugin name header (# PluginName)
            if line.startswith('# '):
                self.current_plugin = line[2:].strip()
                logger.debug(f"Found plugin: {self.current_plugin}")
                
            # Check for config file header (## filename.yml)
            elif line.startswith('## '):
                self.current_file = line[3:].strip()
                logger.debug(f"Found config file: {self.current_file}")
                
            # Check for YAML code block
            elif line.startswith('```yaml') or line.startswith('```yml'):
                yaml_content, i = self._extract_yaml_block(lines, i + 1)
                if yaml_content and self.current_plugin and self.current_file:
                    parsed = self._parse_yaml_content(
                        yaml_content, 
                        self.current_plugin,
                        self.current_file
                    )
                    configs.extend(parsed)
                continue  # i already advanced by _extract_yaml_block
                
            i += 1
        
        return configs
    
    def _extract_yaml_block(self, lines: List[str], start_index: int) -> Tuple[str, int]:
        """
        Extract YAML content from code block.
        
        Args:
            lines: All lines from the file
            start_index: Index where YAML content starts
            
        Returns:
            Tuple of (yaml_content, next_line_index)
        """
        yaml_lines = []
        i = start_index
        
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('```'):
                break
            yaml_lines.append(line)
            i += 1
        
        return '\n'.join(yaml_lines), i + 1
    
    def _parse_yaml_content(
        self, 
        yaml_content: str, 
        plugin_id: str, 
        config_file: str
    ) -> List[ParsedConfig]:
        """
        Parse YAML content into flat config entries.
        
        Args:
            yaml_content: YAML string
            plugin_id: Plugin identifier
            config_file: Config filename
            
        Returns:
            List of ParsedConfig objects
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {plugin_id}/{config_file}: {e}")
            return []
        
        if not isinstance(data, dict):
            logger.warning(f"YAML root is not dict in {plugin_id}/{config_file}")
            return []
        
        configs = []
        self._flatten_dict(data, plugin_id, config_file, '', configs)
        return configs
    
    def _flatten_dict(
        self, 
        data: Dict[str, Any], 
        plugin_id: str,
        config_file: str,
        prefix: str,
        configs: List[ParsedConfig]
    ):
        """
        Recursively flatten nested dict into dot-notation config keys.
        
        Args:
            data: Dictionary to flatten
            plugin_id: Plugin identifier
            config_file: Config filename
            prefix: Current key prefix (for nested keys)
            configs: List to append ParsedConfig objects to
        """
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recurse into nested dict
                self._flatten_dict(value, plugin_id, config_file, full_key, configs)
            else:
                # Leaf value - create config entry
                value_type = self._determine_value_type(value)
                configs.append(ParsedConfig(
                    plugin_id=plugin_id,
                    config_file=config_file,
                    config_key=full_key,
                    config_value=value,
                    value_type=value_type,
                    scope_level="GLOBAL",
                    notes=f"Parsed from baseline markdown"
                ))
    
    def _determine_value_type(self, value: Any) -> str:
        """
        Determine the value type for database storage.
        
        Args:
            value: The value to categorize
            
        Returns:
            Type string: 'string', 'integer', 'float', 'boolean', 'list', 'dict'
        """
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        else:
            return 'string'
    
    def parse_baseline_directory(self, directory: Path) -> Dict[str, List[ParsedConfig]]:
        """
        Parse all baseline markdown files in a directory.
        
        Args:
            directory: Path to directory containing baseline files
            
        Returns:
            Dict mapping filename to list of ParsedConfig objects
        """
        if not directory.exists():
            raise FileNotFoundError(f"Baseline directory not found: {directory}")
        
        results = {}
        for md_file in directory.glob('*.md'):
            try:
                configs = self.parse_baseline_file(md_file)
                results[md_file.stem] = configs
                logger.info(f"Parsed {len(configs)} configs from {md_file.name}")
            except Exception as e:
                logger.error(f"Failed to parse {md_file.name}: {e}")
        
        return results


class BaselineToDatabase:
    """Convert parsed baselines into database records"""
    
    def __init__(self, db_connection):
        """
        Initialize with database connection.
        
        Args:
            db_connection: Database connection object (e.g., mysql.connector connection)
        """
        self.db = db_connection
    
    def insert_config_rule(self, config: ParsedConfig, priority: int = 0) -> int:
        """
        Insert a parsed config into config_rules table.
        
        Args:
            config: ParsedConfig object
            priority: Priority for this rule (default 0)
            
        Returns:
            The inserted rule_id
        """
        import json
        
        cursor = self.db.cursor()
        
        # Encode value as JSON
        config_value_json = json.dumps(config.config_value)
        
        query = """
        INSERT INTO config_rules (
            scope_level,
            server_name, meta_tag_id, instance_id, world_name, rank_name, player_uuid,
            plugin_id, config_file, config_key, config_value, value_type,
            priority, notes, is_active
        ) VALUES (
            %s, 
            NULL, NULL, NULL, NULL, NULL, NULL,
            %s, %s, %s, %s, %s,
            %s, %s, TRUE
        )
        """
        
        cursor.execute(query, (
            config.scope_level,
            config.plugin_id,
            config.config_file,
            config.config_key,
            config_value_json,
            config.value_type,
            priority,
            config.notes
        ))
        
        self.db.commit()
        return cursor.lastrowid
    
    def bulk_insert_configs(self, configs: List[ParsedConfig], priority: int = 0) -> int:
        """
        Bulk insert multiple configs.
        
        Args:
            configs: List of ParsedConfig objects
            priority: Priority for all rules (default 0)
            
        Returns:
            Number of rows inserted
        """
        import json
        
        if not configs:
            return 0
        
        cursor = self.db.cursor()
        
        query = """
        INSERT INTO config_rules (
            scope_level,
            server_name, meta_tag_id, instance_id, world_name, rank_name, player_uuid,
            plugin_id, config_file, config_key, config_value, value_type,
            priority, notes, is_active
        ) VALUES (
            %s, 
            NULL, NULL, NULL, NULL, NULL, NULL,
            %s, %s, %s, %s, %s,
            %s, %s, TRUE
        )
        """
        
        values = [
            (
                config.scope_level,
                config.plugin_id,
                config.config_file,
                config.config_key,
                json.dumps(config.config_value),
                config.value_type,
                priority,
                config.notes
            )
            for config in configs
        ]
        
        cursor.executemany(query, values)
        self.db.commit()
        
        return cursor.rowcount
    
    def import_baseline_file(self, file_path: Path, priority: int = 0) -> int:
        """
        Parse and import a baseline file into database.
        
        Args:
            file_path: Path to baseline markdown file
            priority: Priority for all rules
            
        Returns:
            Number of rules inserted
        """
        parser = BaselineParser()
        configs = parser.parse_baseline_file(file_path)
        return self.bulk_insert_configs(configs, priority)
    
    def import_baseline_directory(self, directory: Path, priority: int = 0) -> Dict[str, int]:
        """
        Parse and import all baseline files in directory.
        
        Args:
            directory: Path to directory containing baselines
            priority: Priority for all rules
            
        Returns:
            Dict mapping filename to number of rules inserted
        """
        parser = BaselineParser()
        all_results = parser.parse_baseline_directory(directory)
        
        results = {}
        for filename, configs in all_results.items():
            count = self.bulk_insert_configs(configs, priority)
            results[filename] = count
            logger.info(f"Imported {count} rules from {filename}")
        
        return results


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Example: Parse a single baseline file
    parser = BaselineParser()
    
    baseline_path = Path("utildata/baselines/EssentialsX.md")
    if baseline_path.exists():
        configs = parser.parse_baseline_file(baseline_path)
        print(f"\nParsed {len(configs)} config entries:")
        for config in configs[:5]:  # Show first 5
            print(f"  {config.plugin_id}/{config.config_file} -> {config.config_key} = {config.config_value}")
    
    # Example: Import to database (requires connection)
    # import mysql.connector
    # db = mysql.connector.connect(
    #     host='135.181.212.169',
    #     port=3369,
    #     user='sqlworkerSMP',
    #     password='SQLdb2024!',
    #     database='archivesmp_config'
    # )
    # 
    # importer = BaselineToDatabase(db)
    # count = importer.import_baseline_file(baseline_path, priority=10)
    # print(f"Imported {count} rules to database")
    # 
    # db.close()
