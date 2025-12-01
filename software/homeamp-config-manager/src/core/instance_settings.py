"""
Instance Settings Module

Manages per-instance configuration including update modes, auto-deployment settings,
and plugin preferences.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class UpdateMode(str, Enum):
    """Plugin update deployment modes"""
    MANUAL = "manual"           # User must manually trigger all updates
    SEMI_AUTO = "semi_auto"     # Updates stage automatically, user triggers deployment
    FULL_AUTO = "full_auto"     # Updates download and deploy automatically


class InstanceSettings(BaseModel):
    """Per-instance configuration settings"""
    instance_name: str
    update_mode: UpdateMode = UpdateMode.MANUAL
    auto_deploy_low_risk: bool = False      # Auto-deploy low-risk updates
    auto_deploy_medium_risk: bool = False   # Auto-deploy medium-risk updates
    auto_deploy_high_risk: bool = False     # Never auto-deploy high-risk (override)
    excluded_plugins: list[str] = []        # Plugins to never auto-update
    preferred_channels: Dict[str, str] = {} # Per-plugin channel (stable/beta/dev)
    maintenance_window_start: Optional[str] = None  # HH:MM format
    maintenance_window_end: Optional[str] = None
    max_updates_per_cycle: int = 3          # Max plugin updates in one cycle
    require_restart_approval: bool = True   # Require approval for server restarts


class InstanceSettingsManager:
    """Manages instance settings persistence"""
    
    def __init__(self, data_dir: Path):
        """
        Initialize settings manager
        
        Args:
            data_dir: Directory to store instance settings
        """
        self.data_dir = Path(data_dir)
        self.settings_file = self.data_dir / "instance_settings.json"
        self.settings_cache: Dict[str, InstanceSettings] = {}
        self._load_settings()
    
    def _load_settings(self):
        """Load all instance settings from disk"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    for instance_name, settings_dict in data.items():
                        self.settings_cache[instance_name] = InstanceSettings(**settings_dict)
                logger.info(f"Loaded settings for {len(self.settings_cache)} instances")
        except Exception as e:
            logger.error(f"Failed to load instance settings: {e}")
    
    def _save_settings(self):
        """Save all instance settings to disk"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            data = {
                name: settings.dict()
                for name, settings in self.settings_cache.items()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved settings for {len(self.settings_cache)} instances")
        except Exception as e:
            logger.error(f"Failed to save instance settings: {e}")
    
    def get_settings(self, instance_name: str) -> InstanceSettings:
        """
        Get settings for an instance (creates defaults if not exists)
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            InstanceSettings for the instance
        """
        if instance_name not in self.settings_cache:
            # Create default settings
            self.settings_cache[instance_name] = InstanceSettings(
                instance_name=instance_name
            )
            self._save_settings()
        
        return self.settings_cache[instance_name]
    
    def update_settings(self, instance_name: str, updates: Dict[str, Any]) -> InstanceSettings:
        """
        Update settings for an instance
        
        Args:
            instance_name: Name of the instance
            updates: Dictionary of fields to update
            
        Returns:
            Updated InstanceSettings
        """
        current = self.get_settings(instance_name)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(current, key):
                setattr(current, key, value)
        
        self.settings_cache[instance_name] = current
        self._save_settings()
        
        return current
    
    def get_all_settings(self) -> Dict[str, InstanceSettings]:
        """Get settings for all instances"""
        return self.settings_cache.copy()
    
    def should_auto_deploy(self, instance_name: str, risk_level: str) -> bool:
        """
        Check if plugin update should be auto-deployed based on instance settings
        
        Args:
            instance_name: Name of the instance
            risk_level: Risk level of the update (low/medium/high/critical)
            
        Returns:
            True if should auto-deploy
        """
        settings = self.get_settings(instance_name)
        
        # Check update mode
        if settings.update_mode == UpdateMode.MANUAL:
            return False
        
        if settings.update_mode == UpdateMode.SEMI_AUTO:
            return False  # Semi-auto only stages, doesn't deploy
        
        # Full auto mode - check risk level permissions
        if risk_level in ['high', 'critical']:
            return settings.auto_deploy_high_risk  # Should always be False
        elif risk_level == 'medium':
            return settings.auto_deploy_medium_risk
        elif risk_level == 'low':
            return settings.auto_deploy_low_risk
        
        return False
    
    def is_plugin_excluded(self, instance_name: str, plugin_name: str) -> bool:
        """Check if plugin is excluded from auto-updates"""
        settings = self.get_settings(instance_name)
        return plugin_name in settings.excluded_plugins
    
    def in_maintenance_window(self, instance_name: str) -> bool:
        """Check if current time is within maintenance window"""
        settings = self.get_settings(instance_name)
        
        if not settings.maintenance_window_start or not settings.maintenance_window_end:
            return True  # No window defined = always allowed
        
        try:
            from datetime import datetime
            now = datetime.now().time()
            start = datetime.strptime(settings.maintenance_window_start, "%H:%M").time()
            end = datetime.strptime(settings.maintenance_window_end, "%H:%M").time()
            
            if start <= end:
                return start <= now <= end
            else:
                # Window crosses midnight
                return now >= start or now <= end
        except Exception as e:
            logger.error(f"Error checking maintenance window: {e}")
            return True  # Default to allowing updates
