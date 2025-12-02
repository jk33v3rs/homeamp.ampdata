"""
Agent REST API for receiving config deployment and restart commands.

This API runs alongside the agent service on both Hetzner and OVH agents
to receive commands from the web UI.

Integrates with existing AgentService from service.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess
import logging
import json
from datetime import datetime

logger = logging.getLogger('archivesmp-agent-api')

app = FastAPI(
    title="ArchiveSMP Agent API",
    description="REST API for config deployment and instance management",
    version="1.0.0"
)

# Global agent service instance (set during startup)
agent_service = None


def set_agent_service(service):
    """Set the agent service instance for API to use"""
    global agent_service
    agent_service = service


class ConfigDeploymentRequest(BaseModel):
    """Request to deploy configs to specific instances"""
    configs: Dict[str, Dict[str, Any]]  # {instance_name: {plugin_name: config_data}}
    requester: str
    timestamp: str


class RestartRequest(BaseModel):
    """Request to restart specific instances"""
    instances: List[str]  # List of instance shortnames (e.g., ["BENT01", "CLIP01"])
    restart_all: bool = False


class AgentStatus(BaseModel):
    """Agent status response"""
    server_name: str
    instances: List[str]
    needs_restart: List[str]
    last_config_update: Optional[str]
    agent_version: str


# Track which instances need restart
needs_restart_instances: set = set()

# Track last config deployment time
last_config_deployment: Optional[datetime] = None


@app.get("/api/agent/status")
async def get_agent_status() -> AgentStatus:
    """Get current agent status"""
    try:
        # Discover instances
        instances = _discover_instances()
        
        return AgentStatus(
            server_name=_get_server_name(),
            instances=instances,
            needs_restart=list(needs_restart_instances),
            last_config_update=last_config_deployment.isoformat() if last_config_deployment else None,
            agent_version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/deploy-configs")
async def deploy_configs(request: ConfigDeploymentRequest) -> Dict[str, Any]:
    """
    Deploy configurations to specified instances.
    
    Args:
        request: Config deployment request containing instance->plugin->config mappings
        
    Returns:
        Deployment result with success/failure per instance
    """
    global last_config_deployment
    results = {}
    
    for instance_name, plugins_config in request.configs.items():
        try:
            # Get instance path
            instance_path = Path(f"/home/amp/.ampdata/instances/{instance_name}")
            
            if not instance_path.exists():
                results[instance_name] = {
                    "success": False,
                    "error": f"Instance directory not found: {instance_path}"
                }
                continue
            
            # Deploy each plugin config
            plugin_results = {}
            for plugin_name, config_data in plugins_config.items():
                try:
                    plugin_result = _deploy_plugin_config(
                        instance_path, 
                        plugin_name, 
                        config_data
                    )
                    plugin_results[plugin_name] = plugin_result
                    
                except Exception as e:
                    plugin_results[plugin_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if all plugins deployed successfully
            all_success = all(r.get("success", False) for r in plugin_results.values())
            
            results[instance_name] = {
                "success": all_success,
                "plugins": plugin_results
            }
            
            # Mark instance as needing restart if any config changed
            if all_success:
                needs_restart_instances.add(instance_name)
                logger.info(f"Instance {instance_name} marked for restart")
            
        except Exception as e:
            results[instance_name] = {
                "success": False,
                "error": str(e)
            }
    
    # Update last deployment timestamp if any deployment succeeded
    if any(r.get("success", False) for r in results.values()):
        last_config_deployment = datetime.now()
    
    return {
        "success": all(r.get("success", False) for r in results.values()),
        "results": results,
        "timestamp": datetime.now().isoformat(),
        "needs_restart": list(needs_restart_instances)
    }


@app.post("/api/agent/restart")
async def restart_instances(request: RestartRequest) -> Dict[str, Any]:
    """
    Restart AMP instances using ampinstmgr commands.
    
    Args:
        request: Restart request specifying which instances to restart
        
    Returns:
        Restart execution results
    """
    try:
        if request.restart_all:
            # Restart all instances on this server
            result = _execute_amp_command("restartAll")
            
            # Clear all restart flags on success
            if result["success"]:
                needs_restart_instances.clear()
            
            return {
                "success": result["success"],
                "command": "restartAll",
                "output": result.get("output", ""),
                "error": result.get("error", "")
            }
        else:
            # Restart specific instances
            restart_results = {}
            
            for instance in request.instances:
                result = _execute_amp_command("restart", instance)
                restart_results[instance] = result
                
                # Remove from needs_restart on success
                if result["success"] and instance in needs_restart_instances:
                    needs_restart_instances.remove(instance)
            
            return {
                "success": all(r.get("success", False) for r in restart_results.values()),
                "results": restart_results,
                "needs_restart": list(needs_restart_instances)
            }
            
    except Exception as e:
        logger.error(f"Restart command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/mark-restart-needed")
async def mark_restart_needed(instance_name: str) -> Dict[str, Any]:
    """Mark an instance as needing restart (e.g., after plugin update)"""
    needs_restart_instances.add(instance_name)
    return {
        "success": True,
        "instance": instance_name,
        "needs_restart": list(needs_restart_instances)
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _discover_instances() -> List[str]:
    """Discover all AMP instances on this server"""
    if agent_service:
        return agent_service.managed_instances
    
    # Fallback if service not initialized
    instances_dir = Path('/home/amp/.ampdata/instances')
    
    if not instances_dir.exists():
        return []
    
    instances = []
    for item in instances_dir.iterdir():
        if item.is_dir() and (item / 'AMPConfig.conf').exists():
            instances.append(item.name)
    
    return sorted(instances)


def _get_server_name() -> str:
    """Get the physical server name (Hetzner or OVH)"""
    if agent_service:
        return agent_service.physical_server
    
    # Fallback: try to read from hostname or config
    import socket
    hostname = socket.gethostname().lower()
    if 'hetzner' in hostname:
        return 'Hetzner'
    elif 'ovh' in hostname:
        return 'OVH'
    return "unknown"


def _deploy_plugin_config(instance_path: Path, plugin_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploy a plugin configuration to an instance using existing ConfigUpdater.
    
    Args:
        instance_path: Path to instance directory
        plugin_name: Name of the plugin
        config_data: Configuration data to write
        
    Returns:
        Deployment result
    """
    try:
        # Use the existing ConfigUpdater if agent_service is available
        if agent_service and hasattr(agent_service, 'config_updater'):
            updater = agent_service.config_updater
            # Create a change request format that ConfigUpdater expects
            change_request = {
                'instance': instance_path.name,
                'plugin': plugin_name,
                'config_data': config_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Apply using existing updater
            result = updater.apply_change(change_request)
            
            if result.get('success'):
                needs_restart_instances.add(instance_path.name)
                logger.info(f"Successfully deployed {plugin_name} config to {instance_path.name}")
            
            return result
        
        # Fallback: manual deployment if service not available
        # Determine config file path based on plugin
        config_file = instance_path / "Minecraft" / "plugins" / plugin_name / "config.yml"
        
        # Some plugins have different structures
        if plugin_name == "LevelledMobs":
            config_file = instance_path / "Minecraft" / "plugins" / "LevelledMobs" / "settings.yml"
        elif plugin_name == "CMI":
            config_file = instance_path / "Minecraft" / "plugins" / "CMI" / "config.yml"
        
        # Backup existing config if it exists
        if config_file.exists():
            backup_file = config_file.parent / f"{config_file.name}.backup.{int(datetime.now().timestamp())}"
            import shutil
            shutil.copy2(config_file, backup_file)
            logger.info(f"Backed up {config_file} to {backup_file}")
        
        # Ensure parent directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write new config
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        # Verify write succeeded by reading back
        with open(config_file, 'r') as f:
            written_data = yaml.safe_load(f)
        
        # Basic verification that file was written
        if not written_data:
            raise Exception("Config file verification failed - file is empty")
        
        needs_restart_instances.add(instance_path.name)
        logger.info(f"Successfully deployed {plugin_name} config to {instance_path.name}")
        
        return {
            "success": True,
            "plugin": plugin_name,
            "instance": instance_path.name,
            "config_file": str(config_file),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to deploy {plugin_name} config to {instance_path.name}: {e}")
        return {
            "success": False,
            "plugin": plugin_name,
            "instance": instance_path.name,
            "error": str(e)
        }


def _execute_amp_command(command: str, instance: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute ampinstmgr command.
    
    Args:
        command: Command to execute (restart, restartAll, stopAll, startAll, updateAll)
        instance: Instance shortname (only for instance-specific commands)
        
    Returns:
        Command execution result
    """
    try:
        # Validate command - whitelist only
        allowed_commands = ['restart', 'restartAll', 'stopAll', 'startAll', 'updateAll', 'stop', 'start']
        if command not in allowed_commands:
            logger.error(f"Invalid command: {command}")
            return {
                "success": False,
                "command": command,
                "error": f"Invalid command. Allowed: {allowed_commands}"
            }
        
        # Validate instance name if provided (alphanumeric + underscores only)
        if instance:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', instance):
                logger.error(f"Invalid instance name: {instance}")
                return {
                    "success": False,
                    "command": command,
                    "error": "Invalid instance name format"
                }
        
        # Build command
        if instance:
            cmd = ["sudo", "-u", "amp", "sudo", "ampinstmgr", command, instance]
        else:
            cmd = ["sudo", "-u", "amp", "sudo", "ampinstmgr", command]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        success = result.returncode == 0
        
        if success:
            logger.info(f"Command succeeded: {' '.join(cmd)}")
        else:
            logger.error(f"Command failed: {' '.join(cmd)}\nStderr: {result.stderr}")
        
        return {
            "success": success,
            "command": ' '.join(cmd),
            "returncode": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {
            "success": False,
            "command": command,
            "error": "Command timed out after 5 minutes"
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "command": command,
            "error": str(e)
        }


# Pl3xMap tile sync endpoints
tile_sync_service = None


@app.post("/api/agent/start-tile-sync")
async def start_tile_sync():
    """Start the Pl3xMap tile sync service"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", "pl3xmap-tile-sync"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {"message": "Tile sync service started", "status": "running"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start service: {result.stderr}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/stop-tile-sync")
async def stop_tile_sync():
    """Stop the Pl3xMap tile sync service"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", "pl3xmap-tile-sync"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {"message": "Tile sync service stopped", "status": "stopped"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to stop service: {result.stderr}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/tile-sync-status")
async def get_tile_sync_status():
    """Get status of tile sync service"""
    try:
        # Check systemd service status
        result = subprocess.run(
            ["systemctl", "is-active", "pl3xmap-tile-sync"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        status = "running" if result.stdout.strip() == "active" else "stopped"
        
        # Get watched instances (if service is running)
        instances = []
        if status == "running" and agent_service and hasattr(agent_service, 'tile_watcher'):
            instances = list(agent_service.tile_watcher.watched_instances)
        
        return {
            "status": status,
            "instances": instances,
            "service": "pl3xmap-tile-sync"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

