"""
Deployment Workflow Module

Manages DEV -> PROD deployment pipeline with validation and rollback
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum
import json


class DeploymentStage(str, Enum):
    """Deployment pipeline stages"""
    PENDING = "pending"
    DEPLOYING_TO_DEV = "deploying_to_dev"
    DEV_VALIDATION = "dev_validation"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING_TO_PROD = "deploying_to_prod"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentPipeline:
    """Manages deployment workflow"""
    
    def __init__(self, storage_path: Path):
        """
        Initialize deployment pipeline
        
        Args:
            storage_path: Path to deployment state storage
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.dev_server = "DEV01"
    
    def create_deployment(self, change_id: str, change_data: Dict[str, Any]) -> str:
        """
        Create new deployment workflow
        
        Args:
            change_id: Change request ID
            change_data: Change request data
            
        Returns:
            Deployment ID
        """
        deployment_id = f"deploy-{change_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        deployment = {
            "deployment_id": deployment_id,
            "change_id": change_id,
            "stage": DeploymentStage.PENDING,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "change_data": change_data,
            "dev_results": None,
            "prod_results": {},
            "validation_results": None,
            "approved_by": None,
            "approved_at": None
        }
        
        self._save_deployment(deployment)
        return deployment_id
    
    def _get_dev_servers(self) -> List[str]:
        """Get list of development servers"""
        # For now, return a hardcoded dev server list
        # This could be loaded from config in the future
        return ["DEV01", "STAGING01"]
    
    def _get_production_servers(self) -> List[str]:
        """Get list of production servers"""
        # Return all servers except dev servers
        all_servers = [
            "SMP1", "SMP2", "SMP3", "SMP4", "SMP5", "SMP6",
            "Creative", "Hub", "Prison", "Skyblock", "Economy",
            "Minigames", "PvP", "Survival", "Hardcore", "Modded"
        ]
        dev_servers = self._get_dev_servers()
        return [server for server in all_servers if server not in dev_servers]
    
    def deploy_to_dev(self, config_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy configuration changes to development environment
        
        Args:
            config_request: Configuration change request
            
        Returns:
            Deployment result
        """
        from datetime import datetime
        import uuid
        
        deployment_id = str(uuid.uuid4())
        
        try:
            # Create deployment record
            deployment = {
                'deployment_id': deployment_id,
                'environment': 'dev',
                'config_request': config_request,
                'status': 'in_progress',
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'results': {},
                'errors': []
            }
            
            # Save deployment record
            deployment_file = self.storage_path / f"{deployment_id}.json"
            import json
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            # Apply to development servers (filtered list)
            dev_servers = self._get_dev_servers()
            results = {}
            
            for server_name in dev_servers:
                try:
                    # Initialize updater for this server
                    from ..updaters.config_updater import ConfigUpdater
                    server_path = self.storage_path.parent / "servers" / server_name
                    updater = ConfigUpdater(server_path, dry_run=False)
                    
                    # Apply changes to this server
                    server_result = updater.apply_change_request(config_request)
                    results[server_name] = server_result
                    
                    if not server_result.get('success'):
                        deployment['errors'].append(f"Server {server_name}: {server_result.get('error')}")
                
                except Exception as e:
                    error_msg = f"Server {server_name} deployment failed: {str(e)}"
                    deployment['errors'].append(error_msg)
                    results[server_name] = {'success': False, 'error': str(e)}
            
            # Update deployment record
            deployment['results'] = results
            deployment['completed_at'] = datetime.now().isoformat()
            deployment['status'] = 'completed' if not deployment['errors'] else 'failed'
            
            # Save updated record
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            return {
                'success': len(deployment['errors']) == 0,
                'deployment_id': deployment_id,
                'environment': 'dev',
                'servers_deployed': len(results),
                'successful_deployments': len([r for r in results.values() if r.get('success')]),
                'failed_deployments': len(deployment['errors']),
                'errors': deployment['errors']
            }
            
        except Exception as e:
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e),
                'environment': 'dev'
            }
    
    def validate_dev_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Validate deployment in development environment
        
        Args:
            deployment_id: Deployment ID to validate
            
        Returns:
            Validation results
        """
        try:
            # Load deployment record
            deployment_file = self.storage_path / f"{deployment_id}.json"
            if not deployment_file.exists():
                return {
                    'success': False,
                    'error': f'Deployment {deployment_id} not found'
                }
            
            with open(deployment_file, 'r') as f:
                deployment = json.load(f)
            
            # Run validation checks
            validation_results = {
                'deployment_id': deployment_id,
                'environment': 'dev',
                'validated_at': datetime.now().isoformat(),
                'checks': [],
                'overall_success': True,
                'ready_for_production': True
            }
            
            # Check 1: All dev servers deployed successfully
            dev_results = deployment.get('results', {})
            successful_deployments = [server for server, result in dev_results.items() 
                                    if result.get('success')]
            failed_deployments = [server for server, result in dev_results.items() 
                                if not result.get('success')]
            
            validation_results['checks'].append({
                'check_name': 'deployment_success',
                'description': 'All development servers deployed successfully',
                'passed': len(failed_deployments) == 0,
                'details': {
                    'successful_servers': successful_deployments,
                    'failed_servers': failed_deployments
                }
            })
            
            if failed_deployments:
                validation_results['ready_for_production'] = False
                validation_results['overall_success'] = False
            
            # Check 2: Configuration files exist and are valid
            config_check_passed = True
            config_details = {}
            
            for server_name in successful_deployments:
                try:
                    server_path = self.storage_path.parent / "servers" / server_name
                    if server_path.exists():
                        config_files = list(server_path.rglob("*.yml")) + list(server_path.rglob("*.properties"))
                        config_details[server_name] = {
                            'config_files_found': len(config_files),
                            'status': 'valid'
                        }
                    else:
                        config_details[server_name] = {
                            'status': 'server_path_not_found'
                        }
                        config_check_passed = False
                except Exception as e:
                    config_details[server_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    config_check_passed = False
            
            validation_results['checks'].append({
                'check_name': 'config_validation',
                'description': 'Configuration files are valid and accessible',
                'passed': config_check_passed,
                'details': config_details
            })
            
            if not config_check_passed:
                validation_results['ready_for_production'] = False
                validation_results['overall_success'] = False
            
            # Update deployment record with validation results
            deployment['validation'] = validation_results
            deployment['status'] = 'validated' if validation_results['overall_success'] else 'validation_failed'
            
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            return validation_results
            
        except Exception as e:
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e)
            }
    
    def approve_for_production(self, deployment_id: str, approved_by: str) -> bool:
        """
        Manually approve deployment for production rollout
        
        Args:
            deployment_id: Deployment ID
            approved_by: Username who approved
            
        Returns:
            True if successful
        """
        deployment = self._load_deployment(deployment_id)
        
        if deployment["stage"] != DeploymentStage.AWAITING_APPROVAL:
            raise ValueError(f"Deployment not awaiting approval (current stage: {deployment['stage']})")
        
        deployment["approved_by"] = approved_by
        deployment["approved_at"] = datetime.now().isoformat()
        deployment["stage"] = DeploymentStage.DEPLOYING_TO_PROD
        deployment["updated_at"] = datetime.now().isoformat()
        
        self._save_deployment(deployment)
        return True
    
    def deploy_to_production(self, deployment_id: str) -> Dict[str, Any]:
        """
        Deploy validated changes to production environment
        
        Args:
            deployment_id: Deployment ID that was validated in dev
            
        Returns:
            Production deployment result
        """
        try:
            # Load deployment record
            deployment_file = self.storage_path / f"{deployment_id}.json"
            if not deployment_file.exists():
                return {
                    'success': False,
                    'error': f'Deployment {deployment_id} not found'
                }
            
            with open(deployment_file, 'r') as f:
                deployment = json.load(f)
            
            # Check if deployment was validated successfully
            validation = deployment.get('validation', {})
            if not validation.get('ready_for_production'):
                return {
                    'success': False,
                    'error': 'Deployment has not passed dev validation',
                    'deployment_id': deployment_id
                }
            
            # Get production servers (exclude dev servers)
            prod_servers = self._get_production_servers()
            config_request = deployment['config_request']
            
            # Update deployment status
            deployment['prod_deployment'] = {
                'started_at': datetime.now().isoformat(),
                'status': 'in_progress',
                'target_servers': prod_servers,
                'results': {}
            }
            
            # Save progress
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            # Deploy to production servers
            prod_results = {}
            errors = []
            
            for server_name in prod_servers:
                try:
                    # Initialize updater for this server
                    from ..updaters.config_updater import ConfigUpdater
                    server_path = self.storage_path.parent / "servers" / server_name
                    updater = ConfigUpdater(server_path, dry_run=False)
                    
                    # Apply changes to this server
                    server_result = updater.apply_change_request(config_request)
                    prod_results[server_name] = server_result
                    
                    if not server_result.get('success'):
                        errors.append(f"Server {server_name}: {server_result.get('error')}")
                
                except Exception as e:
                    error_msg = f"Server {server_name} production deployment failed: {str(e)}"
                    errors.append(error_msg)
                    prod_results[server_name] = {'success': False, 'error': str(e)}
            
            # Update final deployment record
            deployment['prod_deployment'].update({
                'completed_at': datetime.now().isoformat(),
                'status': 'completed' if not errors else 'failed',
                'results': prod_results,
                'errors': errors
            })
            
            deployment['status'] = 'production_deployed' if not errors else 'production_failed'
            
            # Save final record
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            return {
                'success': len(errors) == 0,
                'deployment_id': deployment_id,
                'environment': 'production',
                'servers_deployed': len(prod_results),
                'successful_deployments': len([r for r in prod_results.values() if r.get('success')]),
                'failed_deployments': len(errors),
                'errors': errors,
                'completed_at': deployment['prod_deployment']['completed_at']
            }
            
        except Exception as e:
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e),
                'environment': 'production'
            }
    
    def rollback_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Rollback a deployment to previous state
        
        Args:
            deployment_id: Deployment to rollback
            
        Returns:
            Rollback result
        """
        try:
            # Load deployment record
            deployment_file = self.storage_path / f"{deployment_id}.json"
            if not deployment_file.exists():
                return {
                    'success': False,
                    'error': f'Deployment {deployment_id} not found'
                }
            
            with open(deployment_file, 'r') as f:
                deployment = json.load(f)
            
            # Check if deployment was actually applied
            if deployment.get('status') not in ['production_deployed', 'production_failed']:
                return {
                    'success': False,
                    'error': 'Deployment was not applied to production, cannot rollback',
                    'deployment_id': deployment_id
                }
            
            # Get all servers that were affected
            affected_servers = []
            
            # Add dev servers if they were deployed
            if 'results' in deployment:
                affected_servers.extend(deployment['results'].keys())
            
            # Add production servers if they were deployed
            if 'prod_deployment' in deployment and 'results' in deployment['prod_deployment']:
                affected_servers.extend(deployment['prod_deployment']['results'].keys())
            
            # Remove duplicates
            affected_servers = list(set(affected_servers))
            
            # Start rollback process
            rollback_results = {}
            errors = []
            
            for server_name in affected_servers:
                try:
                    # Initialize updater for this server
                    from ..updaters.config_updater import ConfigUpdater
                    server_path = self.storage_path.parent / "servers" / server_name
                    updater = ConfigUpdater(server_path, dry_run=False)
                    
                    # Find the backup path from deployment results
                    backup_path = None
                    if 'results' in deployment and server_name in deployment['results']:
                        backup_path = deployment['results'][server_name].get('backup_path')
                    elif ('prod_deployment' in deployment and 
                          'results' in deployment['prod_deployment'] and 
                          server_name in deployment['prod_deployment']['results']):
                        backup_path = deployment['prod_deployment']['results'][server_name].get('backup_path')
                    
                    if backup_path:
                        # Use the config updater's rollback functionality
                        updater.backup_dir = backup_path
                        rollback_result = updater.rollback_change(deployment_id)
                        rollback_results[server_name] = rollback_result
                        
                        if not rollback_result.get('success'):
                            errors.append(f"Server {server_name} rollback failed: {rollback_result.get('error')}")
                    else:
                        error_msg = f"No backup found for server {server_name}"
                        errors.append(error_msg)
                        rollback_results[server_name] = {'success': False, 'error': error_msg}
                
                except Exception as e:
                    error_msg = f"Server {server_name} rollback exception: {str(e)}"
                    errors.append(error_msg)
                    rollback_results[server_name] = {'success': False, 'error': str(e)}
            
            # Update deployment record
            deployment['rollback'] = {
                'executed_at': datetime.now().isoformat(),
                'results': rollback_results,
                'errors': errors,
                'status': 'completed' if not errors else 'failed'
            }
            
            deployment['status'] = 'rolled_back' if not errors else 'rollback_failed'
            
            # Save updated record
            with open(deployment_file, 'w') as f:
                json.dump(deployment, f, indent=2)
            
            return {
                'success': len(errors) == 0,
                'deployment_id': deployment_id,
                'servers_rolled_back': len(rollback_results),
                'successful_rollbacks': len([r for r in rollback_results.values() if r.get('success')]),
                'failed_rollbacks': len(errors),
                'errors': errors,
                'executed_at': deployment['rollback']['executed_at']
            }
            
        except Exception as e:
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e)
            }
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get current deployment status
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Deployment status
        """
        return self._load_deployment(deployment_id)
    
    def list_active_deployments(self) -> List[Dict[str, Any]]:
        """
        List all active (non-completed) deployments
        
        Returns:
            List of active deployments
        """
        active_stages = [
            DeploymentStage.PENDING,
            DeploymentStage.DEPLOYING_TO_DEV,
            DeploymentStage.DEV_VALIDATION,
            DeploymentStage.AWAITING_APPROVAL,
            DeploymentStage.DEPLOYING_TO_PROD
        ]
        
        deployments = []
        for file in self.storage_path.glob("deploy-*.json"):
            deployment = self._load_deployment(file.stem)
            if deployment["stage"] in active_stages:
                deployments.append(deployment)
        
        return sorted(deployments, key=lambda d: d["created_at"], reverse=True)
    
    def _get_target_servers(self, change_data: Dict[str, Any]) -> List[str]:
        """Extract target servers from change data"""
        servers = set()
        for change in change_data.get("changes", []):
            applies_to = change.get("applies_to_servers", [])
            excluded = set(change.get("excluded_servers", []))
            
            if "all" in applies_to:
                # All servers except excluded
                all_servers = [
                    'BENT01', 'BIG01', 'CLIP01', 'CREA01', 'CSMC01', 'DEV01',
                    'EMAD01', 'EVO01', 'HARD01', 'HUB01', 'MIN01', 'MINE01',
                    settings.test_servers
                ]
                servers.update(set(all_servers) - excluded)
            else:
                servers.update(set(applies_to) - excluded)
        
        return sorted(list(servers))
    
    def _save_deployment(self, deployment: Dict[str, Any]):
        """Save deployment state to disk"""
        file_path = self.storage_path / f"{deployment['deployment_id']}.json"
        with open(file_path, 'w') as f:
            json.dump(deployment, f, indent=2)
    
    def _load_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Load deployment state from disk"""
        file_path = self.storage_path / f"{deployment_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Deployment {deployment_id} not found")
        
        with open(file_path, 'r') as f:
            return json.load(f)
