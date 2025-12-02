#!/usr/bin/env python3
"""
Parse markdown config files into SQL database
Extracts YAML blocks, preserves structure, populates config_keys table
"""

import os
import re
import yaml
import mysql.connector
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkdownConfigParser:
    """Parse markdown files with YAML blocks into structured SQL"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db = mysql.connector.connect(**db_config)
        self.cursor = self.db.cursor(dictionary=True)
        
    def extract_yaml_blocks(self, markdown_content: str) -> List[Tuple[str, str]]:
        """Extract YAML code blocks from markdown
        
        Returns:
            List of (filename, yaml_content) tuples
        """
        blocks = []
        
        # Pattern: ```yaml or ```yml followed by optional filename comment
        pattern = r'```(?:yaml|yml)\s*(?:#\s*(.+?))?\n(.*?)```'
        
        for match in re.finditer(pattern, markdown_content, re.DOTALL):
            filename = match.group(1) or 'config.yml'
            yaml_content = match.group(2).strip()
            blocks.append((filename.strip(), yaml_content))
            
        return blocks
    
    def parse_yaml_recursive(
        self, 
        data: Any, 
        path: str = "",
        indent_level: int = 0,
        comments: Dict[str, str] = None
    ) -> List[Dict]:
        """Recursively parse YAML into flat key-value records
        
        Returns list of dicts with:
        - key_path: full.dotted.path
        - value: the actual value
        - data_type: string/int/float/boolean/list/dict
        - whitespace_prefix: spaces for this indentation level
        - comment_pre: comment above this key
        - comment_inline: inline comment
        """
        results = []
        comments = comments or {}
        whitespace = "  " * indent_level  # 2 spaces per level
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Get comments for this key
                comment_pre = comments.get(f"{current_path}_pre", "")
                comment_inline = comments.get(f"{current_path}_inline", "")
                
                if isinstance(value, (dict, list)):
                    # Complex type - recurse but also record the parent
                    data_type = 'dict' if isinstance(value, dict) else 'list'
                    results.append({
                        'key_path': current_path,
                        'value': None,  # Complex types don't have scalar values
                        'data_type': data_type,
                        'whitespace_prefix': whitespace,
                        'comment_pre': comment_pre,
                        'comment_inline': comment_inline
                    })
                    results.extend(
                        self.parse_yaml_recursive(
                            value, 
                            current_path, 
                            indent_level + 1,
                            comments
                        )
                    )
                else:
                    # Scalar value
                    data_type = self._get_data_type(value)
                    results.append({
                        'key_path': current_path,
                        'value': str(value) if value is not None else None,
                        'data_type': data_type,
                        'whitespace_prefix': whitespace,
                        'comment_pre': comment_pre,
                        'comment_inline': comment_inline
                    })
                    
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                if isinstance(item, (dict, list)):
                    results.extend(
                        self.parse_yaml_recursive(
                            item,
                            current_path,
                            indent_level + 1,
                            comments
                        )
                    )
                else:
                    data_type = self._get_data_type(item)
                    results.append({
                        'key_path': current_path,
                        'value': str(item) if item is not None else None,
                        'data_type': data_type,
                        'whitespace_prefix': whitespace,
                        'comment_pre': "",
                        'comment_inline': ""
                    })
                    
        return results
    
    def _get_data_type(self, value: Any) -> str:
        """Determine SQL enum value for data type"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        else:
            return 'string'
    
    def extract_comments(self, yaml_text: str) -> Dict[str, str]:
        """Extract comments from YAML text
        
        Returns dict mapping key_path to comment text
        """
        comments = {}
        lines = yaml_text.split('\n')
        current_path = []
        pending_comment = []
        
        for line in lines:
            # Check for comment
            if '#' in line:
                parts = line.split('#', 1)
                code_part = parts[0].strip()
                comment_part = parts[1].strip()
                
                if not code_part:
                    # Full line comment - save for next key
                    pending_comment.append(comment_part)
                else:
                    # Inline comment
                    # Try to extract key name
                    if ':' in code_part:
                        key = code_part.split(':')[0].strip()
                        path = '.'.join(current_path + [key])
                        comments[f"{path}_inline"] = comment_part
                        
                        if pending_comment:
                            comments[f"{path}_pre"] = '\n'.join(pending_comment)
                            pending_comment = []
            else:
                # No comment, check if it's a key definition
                if ':' in line:
                    key = line.split(':')[0].strip()
                    if key and not key.startswith('-'):
                        path = '.'.join(current_path + [key])
                        if pending_comment:
                            comments[f"{path}_pre"] = '\n'.join(pending_comment)
                            pending_comment = []
                            
        return comments
    
    def get_or_create_plugin(self, plugin_name: str, platform: str = 'universal') -> int:
        """Get plugin ID or create if doesn't exist"""
        self.cursor.execute(
            "SELECT id FROM plugins WHERE plugin_name = %s",
            (plugin_name,)
        )
        result = self.cursor.fetchone()
        
        if result:
            return result['id']
        
        self.cursor.execute(
            """INSERT INTO plugins (plugin_name, platform) 
               VALUES (%s, %s)""",
            (plugin_name, platform)
        )
        self.db.commit()
        return self.cursor.lastrowid
    
    def insert_config_keys(
        self, 
        plugin_id: int, 
        filename: str, 
        keys: List[Dict],
        is_snapshot: bool = True
    ):
        """Insert parsed keys into config_keys table
        
        Args:
            is_snapshot: True if from markdown snapshots (observed_value),
                        False if from plugin defaults (plugin_default_value)
        """
        
        for key_data in keys:
            key_path = key_data['key_path']
            
            # Check if key already exists
            self.cursor.execute(
                """SELECT id FROM config_keys 
                   WHERE plugin_id = %s 
                   AND config_filename = %s 
                   AND key_path = %s""",
                (plugin_id, filename, key_path)
            )
            
            if self.cursor.fetchone():
                logger.debug(f"Key already exists: {key_path}")
                continue
            
            # Determine file type from filename
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                file_type = 'yaml'
            elif filename.endswith('.json'):
                file_type = 'json'
            elif filename.endswith('.properties'):
                file_type = 'properties'
            elif filename.endswith('.toml'):
                file_type = 'toml'
            else:
                file_type = 'yaml'  # default
            
            # Snapshot values go to observed_value, leave plugin_default_value NULL
            # This allows us to later add actual plugin defaults when we get them
            self.cursor.execute(
                """INSERT INTO config_keys (
                    plugin_id, config_filename, file_type, key_path,
                    whitespace_prefix, comment_pre, comment_inline,
                    plugin_default_value, observed_value, data_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    plugin_id,
                    filename,
                    file_type,
                    key_path,
                    key_data['whitespace_prefix'],
                    key_data['comment_pre'],
                    key_data['comment_inline'],
                    None if is_snapshot else key_data['value'],
                    key_data['value'] if is_snapshot else None,
                    key_data['data_type']
                )
            )
        
        self.db.commit()
        logger.info(f"Inserted {len(keys)} keys for {filename}")
    
    def parse_markdown_file(self, markdown_path: Path, plugin_name: str):
        """Parse a single markdown file"""
        logger.info(f"Parsing {markdown_path.name}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML blocks
        yaml_blocks = self.extract_yaml_blocks(content)
        
        if not yaml_blocks:
            logger.warning(f"No YAML blocks found in {markdown_path.name}")
            return
        
        plugin_id = self.get_or_create_plugin(plugin_name)
        
        for filename, yaml_content in yaml_blocks:
            try:
                # Extract comments first
                comments = self.extract_comments(yaml_content)
                
                # Parse YAML
                data = yaml.safe_load(yaml_content)
                
                if not data:
                    logger.warning(f"Empty YAML in {filename}")
                    continue
                
                # Recursively parse into flat structure
                keys = self.parse_yaml_recursive(data, comments=comments)
                
                # Insert into database
                self.insert_config_keys(plugin_id, filename, keys)
                
            except yaml.YAMLError as e:
                logger.error(f"YAML parse error in {filename}: {e}")
                continue
    
    def parse_all_baselines(self, baselines_dir: Path):
        """Parse all markdown files in baselines directory"""
        markdown_files = list(baselines_dir.glob('*_universal_config.md'))
        
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        for md_file in markdown_files:
            # Extract plugin name from filename
            # e.g., "Citizens_universal_config.md" -> "Citizens"
            plugin_name = md_file.stem.replace('_universal_config', '')
            
            self.parse_markdown_file(md_file, plugin_name)
        
        logger.info("✓ All baselines parsed into database")
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.db.close()


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: parse_markdown_to_sql.py <baselines_dir>")
        sys.exit(1)
    
    baselines_dir = Path(sys.argv[1])
    
    if not baselines_dir.exists():
        print(f"Error: Directory not found: {baselines_dir}")
        sys.exit(1)
    
    # Database configuration (from environment or secrets)
    # ISOLATED DATABASE - NOT production asmp_SQL
    db_config = {
        'host': os.getenv('DB_HOST', '135.181.212.169'),
        'port': int(os.getenv('DB_PORT', 3369)),
        'user': os.getenv('DB_USER', 'sqlworkerSMP'),
        'password': os.getenv('DB_PASSWORD'),  # Must be provided
        'database': os.getenv('DB_NAME', 'asmp_config')
    }
    
    if not db_config['password']:
        print("Error: DB_PASSWORD environment variable required")
        sys.exit(1)
    
    parser = MarkdownConfigParser(db_config)
    
    try:
        parser.parse_all_baselines(baselines_dir)
    finally:
        parser.close()


if __name__ == '__main__':
    main()
