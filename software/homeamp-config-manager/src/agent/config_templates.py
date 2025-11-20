"""
Database-backed Config Templates for ArchiveSMP Config Manager

Manages reusable configuration templates stored in database
"""

import mariadb
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger("config_templates")


class ConfigTemplateManager:
    """Manages configuration templates in database"""
    
    def __init__(self, db_connection):
        """
        Initialize template manager
        
        Args:
            db_connection: MariaDB connection
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)
    
    def create_template(
        self,
        template_name: str,
        plugin_name: str,
        template_data: Dict[str, Any],
        description: str = "",
        created_by: str = "system",
        tags: List[str] = None
    ) -> int:
        """
        Create a new config template
        
        Args:
            template_name: Unique template name
            plugin_name: Plugin this template applies to
            template_data: Template configuration data
            description: Template description
            created_by: Username who created it
            tags: Optional tags for categorization
        
        Returns:
            Template ID
        """
        query = """
            INSERT INTO config_templates (
                template_name,
                plugin_name,
                template_data,
                description,
                tags,
                created_by,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        self.cursor.execute(query, (
            template_name,
            plugin_name,
            json.dumps(template_data),
            description,
            ','.join(tags) if tags else None,
            created_by
        ))
        
        self.db.commit()
        template_id = self.cursor.lastrowid
        
        logger.info(f"Created template: {template_name} (ID: {template_id})")
        return template_id
    
    def get_template(self, template_id: int = None, template_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get template by ID or name
        
        Args:
            template_id: Template ID
            template_name: Template name
        
        Returns:
            Template data or None
        """
        if template_id:
            query = "SELECT * FROM config_templates WHERE template_id = %s"
            self.cursor.execute(query, (template_id,))
        elif template_name:
            query = "SELECT * FROM config_templates WHERE template_name = %s"
            self.cursor.execute(query, (template_name,))
        else:
            return None
        
        result = self.cursor.fetchone()
        
        if result and result['template_data']:
            result['template_data'] = json.loads(result['template_data'])
        
        return result
    
    def list_templates(
        self,
        plugin_name: str = None,
        tags: List[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List templates with filters
        
        Args:
            plugin_name: Filter by plugin
            tags: Filter by tags
            limit: Maximum results
        
        Returns:
            List of templates
        """
        query = "SELECT * FROM config_templates WHERE 1=1"
        params = []
        
        if plugin_name:
            query += " AND plugin_name = %s"
            params.append(plugin_name)
        
        if tags:
            for tag in tags:
                query += " AND tags LIKE %s"
                params.append(f"%{tag}%")
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        self.cursor.execute(query, params)
        templates = self.cursor.fetchall()
        
        for template in templates:
            if template['template_data']:
                template['template_data'] = json.loads(template['template_data'])
        
        return templates
    
    def apply_template(
        self,
        template_id: int,
        instance_id: str,
        merge_strategy: str = 'replace'
    ) -> Dict[str, Any]:
        """
        Apply template to an instance
        
        Args:
            template_id: Template to apply
            instance_id: Target instance
            merge_strategy: 'replace' or 'merge'
        
        Returns:
            Result of application
        """
        template = self.get_template(template_id=template_id)
        
        if not template:
            return {"error": "Template not found"}
        
        # Record usage
        query = """
            UPDATE config_templates
            SET usage_count = usage_count + 1,
                last_used_at = NOW()
            WHERE template_id = %s
        """
        self.cursor.execute(query, (template_id,))
        self.db.commit()
        
        logger.info(f"Applied template {template['template_name']} to {instance_id}")
        
        return {
            "success": True,
            "template": template['template_name'],
            "instance": instance_id,
            "strategy": merge_strategy,
            "config_data": template['template_data']
        }
    
    def update_template(
        self,
        template_id: int,
        template_data: Dict[str, Any] = None,
        description: str = None,
        tags: List[str] = None
    ) -> bool:
        """
        Update existing template
        
        Args:
            template_id: Template to update
            template_data: New template data
            description: New description
            tags: New tags
        
        Returns:
            Success status
        """
        updates = []
        params = []
        
        if template_data is not None:
            updates.append("template_data = %s")
            params.append(json.dumps(template_data))
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if tags is not None:
            updates.append("tags = %s")
            params.append(','.join(tags))
        
        if not updates:
            return False
        
        query = f"UPDATE config_templates SET {', '.join(updates)} WHERE template_id = %s"
        params.append(template_id)
        
        self.cursor.execute(query, params)
        self.db.commit()
        
        logger.info(f"Updated template ID {template_id}")
        return True
    
    def delete_template(self, template_id: int) -> bool:
        """
        Delete a template
        
        Args:
            template_id: Template to delete
        
        Returns:
            Success status
        """
        query = "DELETE FROM config_templates WHERE template_id = %s"
        self.cursor.execute(query, (template_id,))
        self.db.commit()
        
        logger.info(f"Deleted template ID {template_id}")
        return self.cursor.rowcount > 0
    
    def clone_from_instance(
        self,
        instance_id: str,
        plugin_name: str,
        template_name: str,
        description: str = "",
        created_by: str = "system"
    ) -> int:
        """
        Create template from existing instance config
        
        Args:
            instance_id: Source instance
            plugin_name: Plugin to clone config from
            template_name: Name for new template
            description: Template description
            created_by: Username
        
        Returns:
            New template ID
        """
        # Get current config from instance
        query = """
            SELECT config_data FROM installed_plugins
            WHERE instance_id = %s AND plugin_name = %s
        """
        self.cursor.execute(query, (instance_id, plugin_name))
        result = self.cursor.fetchone()
        
        if not result or not result['config_data']:
            raise ValueError(f"No config found for {plugin_name} on {instance_id}")
        
        config_data = json.loads(result['config_data'])
        
        return self.create_template(
            template_name=template_name,
            plugin_name=plugin_name,
            template_data=config_data,
            description=description or f"Cloned from {instance_id}",
            created_by=created_by,
            tags=['cloned', instance_id]
        )


def create_template_manager(db_connection) -> ConfigTemplateManager:
    """Factory function to create template manager"""
    return ConfigTemplateManager(db_connection)
