"""
Backward Compatibility Checker for ArchiveSMP Config Manager

Validates plugin version compatibility and dependencies
"""

import mariadb
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger("compatibility_checker")


class CompatibilityChecker:
    """Checks plugin version compatibility"""
    
    def __init__(self, db_connection):
        """
        Initialize compatibility checker
        
        Args:
            db_connection: MariaDB connection
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)
    
    def check_version_compatibility(
        self,
        plugin_name: str,
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        Check if version upgrade is compatible
        
        Args:
            plugin_name: Plugin name
            from_version: Current version
            to_version: Target version
        
        Returns:
            Compatibility report
        """
        result = {
            'compatible': True,
            'breaking_changes': [],
            'migrations_required': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for breaking migrations
        query = """
            SELECT * FROM config_key_migrations
            WHERE plugin_name = %s
            AND is_breaking = 1
            AND (
                (from_version = %s OR from_version LIKE %s)
                OR (to_version = %s OR to_version LIKE %s)
            )
        """
        
        self.cursor.execute(query, (
            plugin_name,
            from_version, f"{from_version.split('.')[0]}.%",
            to_version, f"{to_version.split('.')[0]}.%"
        ))
        
        breaking_migrations = self.cursor.fetchall()
        
        if breaking_migrations:
            result['compatible'] = False
            result['breaking_changes'] = [
                {
                    'key': m['old_key_path'],
                    'new_key': m['new_key_path'],
                    'note': m['notes']
                }
                for m in breaking_migrations
            ]
            result['migrations_required'] = [m['migration_id'] for m in breaking_migrations]
        
        # Check version semver compatibility
        from_major = self._get_major_version(from_version)
        to_major = self._get_major_version(to_version)
        
        if to_major > from_major:
            result['warnings'].append(
                f"Major version upgrade ({from_major} → {to_major}) - review changelog carefully"
            )
            result['recommendations'].append(
                "Test on staging instance before deploying to production"
            )
        
        # Check dependency compatibility
        dependencies = self._check_dependencies(plugin_name, to_version)
        if dependencies:
            result['warnings'].extend(dependencies)
        
        return result
    
    def check_minecraft_compatibility(
        self,
        plugin_name: str,
        plugin_version: str,
        minecraft_version: str
    ) -> Dict[str, Any]:
        """
        Check if plugin version is compatible with Minecraft version
        
        Args:
            plugin_name: Plugin name
            plugin_version: Plugin version
            minecraft_version: Minecraft version (e.g., 1.20.1)
        
        Returns:
            Compatibility report
        """
        # Check plugin metadata
        query = """
            SELECT supported_mc_versions, max_mc_version, min_mc_version
            FROM plugin_metadata
            WHERE plugin_name = %s
        """
        
        self.cursor.execute(query, (plugin_name,))
        metadata = self.cursor.fetchone()
        
        if not metadata:
            return {
                'compatible': 'unknown',
                'warning': 'No compatibility metadata available'
            }
        
        # Parse minecraft version
        mc_ver = self._parse_version(minecraft_version)
        
        if metadata['min_mc_version']:
            min_ver = self._parse_version(metadata['min_mc_version'])
            if mc_ver < min_ver:
                return {
                    'compatible': False,
                    'reason': f"Minecraft {minecraft_version} is below minimum {metadata['min_mc_version']}"
                }
        
        if metadata['max_mc_version']:
            max_ver = self._parse_version(metadata['max_mc_version'])
            if mc_ver > max_ver:
                return {
                    'compatible': False,
                    'reason': f"Minecraft {minecraft_version} is above maximum {metadata['max_mc_version']}"
                }
        
        return {'compatible': True}
    
    def check_plugin_dependencies(
        self,
        plugin_name: str,
        installed_plugins: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Check if plugin dependencies are satisfied
        
        Args:
            plugin_name: Plugin to check
            installed_plugins: List of installed plugins with versions
        
        Returns:
            Dependency report
        """
        query = """
            SELECT required_plugins FROM plugin_metadata
            WHERE plugin_name = %s
        """
        
        self.cursor.execute(query, (plugin_name,))
        result = self.cursor.fetchone()
        
        if not result or not result['required_plugins']:
            return {'satisfied': True, 'missing': [], 'incompatible': []}
        
        # Parse required plugins (format: "PluginName:1.0.0,OtherPlugin:2.0.0")
        import json
        try:
            required = json.loads(result['required_plugins'])
        except:
            required = {}
        
        installed_map = {p['name']: p['version'] for p in installed_plugins}
        
        missing = []
        incompatible = []
        
        for req_plugin, req_version in required.items():
            if req_plugin not in installed_map:
                missing.append({'plugin': req_plugin, 'required_version': req_version})
            else:
                installed_ver = self._parse_version(installed_map[req_plugin])
                required_ver = self._parse_version(req_version)
                
                if installed_ver < required_ver:
                    incompatible.append({
                        'plugin': req_plugin,
                        'installed': installed_map[req_plugin],
                        'required': req_version
                    })
        
        return {
            'satisfied': len(missing) == 0 and len(incompatible) == 0,
            'missing': missing,
            'incompatible': incompatible
        }
    
    def validate_upgrade_path(
        self,
        plugin_name: str,
        from_version: str,
        to_version: str,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Comprehensive upgrade validation
        
        Args:
            plugin_name: Plugin name
            from_version: Current version
            to_version: Target version
            instance_id: Instance to upgrade
        
        Returns:
            Complete validation report
        """
        report = {
            'can_upgrade': True,
            'blockers': [],
            'warnings': [],
            'steps_required': []
        }
        
        # Version compatibility
        compat = self.check_version_compatibility(plugin_name, from_version, to_version)
        
        if not compat['compatible']:
            report['can_upgrade'] = False
            report['blockers'].extend([
                f"Breaking change: {bc['key']} → {bc['new_key']}"
                for bc in compat['breaking_changes']
            ])
            report['steps_required'].append(
                f"Apply {len(compat['migrations_required'])} config migrations"
            )
        
        report['warnings'].extend(compat['warnings'])
        
        # Get instance minecraft version
        query = "SELECT minecraft_version FROM instances WHERE instance_id = %s"
        self.cursor.execute(query, (instance_id,))
        instance = self.cursor.fetchone()
        
        if instance:
            mc_compat = self.check_minecraft_compatibility(
                plugin_name,
                to_version,
                instance['minecraft_version']
            )
            
            if not mc_compat.get('compatible'):
                report['can_upgrade'] = False
                report['blockers'].append(mc_compat.get('reason', 'Minecraft version incompatible'))
        
        # Add recommendations
        if compat['recommendations']:
            report['steps_required'].extend(compat['recommendations'])
        
        return report
    
    def _check_dependencies(self, plugin_name: str, version: str) -> List[str]:
        """Check for dependency warnings"""
        warnings = []
        
        # Check for known problematic combinations
        if plugin_name == 'EliteMobs' and version.startswith('9.'):
            warnings.append("EliteMobs 9.x requires MythicLib 1.6+")
        
        return warnings
    
    def _get_major_version(self, version: str) -> int:
        """Extract major version number"""
        match = re.match(r'(\d+)', version)
        return int(match.group(1)) if match else 0
    
    def _parse_version(self, version: str) -> tuple:
        """Parse version string to tuple for comparison"""
        parts = re.findall(r'\d+', version)
        return tuple(int(p) for p in parts[:3]) if parts else (0, 0, 0)


def create_compatibility_checker(db_connection) -> CompatibilityChecker:
    """Factory function to create compatibility checker"""
    return CompatibilityChecker(db_connection)
