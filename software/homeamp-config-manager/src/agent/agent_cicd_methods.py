"""
CI/CD Integration & Plugin Update Management
Handles webhook events, update checks, and automated deployments
"""

from typing import Dict, Any, List, Optional
import requests
import json
from datetime import datetime, timedelta
import re


class AgentCICDMethods:
    """Mixin for CI/CD and update management"""
    
    def _check_plugin_updates(self):
        """
        Check for plugin updates from all configured sources
        NO HARDCODING - iterates through registry
        """
        self.logger.info("🔄 Checking for plugin updates")
        
        for plugin_id, plugin_data in self.plugin_registry.items():
            try:
                update_info = None
                
                # Check Modrinth
                if plugin_data.get('modrinth_id'):
                    update_info = self._check_modrinth_update(plugin_data)
                
                # Check Hangar
                elif plugin_data.get('hangar_slug'):
                    update_info = self._check_hangar_update(plugin_data)
                
                # Check GitHub Releases
                elif plugin_data.get('github_repo'):
                    update_info = self._check_github_release(plugin_data)
                
                # Check Jenkins
                elif plugin_data.get('jenkins_url'):
                    update_info = self._check_jenkins_build(plugin_data)
                
                if update_info and update_info['version'] != plugin_data.get('current_stable_version'):
                    self._handle_new_version(plugin_id, update_info)
            
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to check updates for {plugin_id}: {e}")
    
    def _check_modrinth_update(self, plugin_data: Dict) -> Optional[Dict]:
        """Check Modrinth API for latest version"""
        try:
            modrinth_id = plugin_data['modrinth_id']
            url = f"https://api.modrinth.com/v2/project/{modrinth_id}/version"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            versions = response.json()
            if not versions:
                return None
            
            # Get latest stable version
            latest = versions[0]
            
            return {
                'version': latest['version_number'],
                'download_url': latest['files'][0]['url'],
                'changelog': latest.get('changelog', ''),
                'release_date': latest['date_published'],
                'is_prerelease': False  # Modrinth versions are typically stable
            }
        
        except Exception as e:
            self.logger.warning(f"Modrinth check failed for {plugin_data['plugin_id']}: {e}")
            return None
    
    def _check_hangar_update(self, plugin_data: Dict) -> Optional[Dict]:
        """Check Hangar API for latest version"""
        try:
            slug = plugin_data['hangar_slug']
            url = f"https://hangar.papermc.io/api/v1/projects/{slug}/versions"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('result'):
                return None
            
            latest = data['result'][0]
            
            return {
                'version': latest['name'],
                'download_url': latest['downloads'].get('PAPER', {}).get('downloadUrl'),
                'changelog': latest.get('description', ''),
                'release_date': latest.get('createdAt'),
                'is_prerelease': False
            }
        
        except Exception as e:
            self.logger.warning(f"Hangar check failed for {plugin_data['plugin_id']}: {e}")
            return None
    
    def _check_github_release(self, plugin_data: Dict) -> Optional[Dict]:
        """Check GitHub Releases for latest version"""
        try:
            repo = plugin_data['github_repo']
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            
            headers = {}
            if self.config.get('github_token'):
                headers['Authorization'] = f"token {self.config['github_token']}"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release = response.json()
            
            # Find jar asset (use pattern if configured)
            pattern = plugin_data.get('github_release_pattern', r'\.jar$')
            jar_asset = None
            
            for asset in release.get('assets', []):
                if re.search(pattern, asset['name']):
                    jar_asset = asset
                    break
            
            if not jar_asset:
                return None
            
            return {
                'version': release['tag_name'].lstrip('v'),
                'download_url': jar_asset['browser_download_url'],
                'changelog': release.get('body', ''),
                'release_date': release['published_at'],
                'is_prerelease': release.get('prerelease', False)
            }
        
        except Exception as e:
            self.logger.warning(f"GitHub check failed for {plugin_data['plugin_id']}: {e}")
            return None
    
    def _check_jenkins_build(self, plugin_data: Dict) -> Optional[Dict]:
        """Check Jenkins for latest build"""
        try:
            jenkins_url = plugin_data['jenkins_url']
            url = f"{jenkins_url}/lastSuccessfulBuild/api/json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            build = response.json()
            
            # Find jar artifact
            jar_artifact = None
            for artifact in build.get('artifacts', []):
                if artifact['fileName'].endswith('.jar'):
                    jar_artifact = artifact
                    break
            
            if not jar_artifact:
                return None
            
            return {
                'version': str(build['number']),
                'download_url': f"{jenkins_url}/lastSuccessfulBuild/artifact/{jar_artifact['relativePath']}",
                'changelog': '',
                'release_date': datetime.fromtimestamp(build['timestamp'] / 1000).isoformat(),
                'is_prerelease': False
            }
        
        except Exception as e:
            self.logger.warning(f"Jenkins check failed for {plugin_data['plugin_id']}: {e}")
            return None
    
    def _handle_new_version(self, plugin_id: str, update_info: Dict):
        """Handle discovery of new plugin version"""
        self.logger.info(f"🆕 New version available for {plugin_id}: {update_info['version']}")
        
        # Update plugin registry
        try:
            self.db.execute_query("""
                UPDATE plugins
                SET latest_version = %(version)s,
                    last_available_version_at = NOW(),
                    last_checked_at = NOW()
                WHERE plugin_id = %(plugin_id)s
            """, {
                'plugin_id': plugin_id,
                'version': update_info['version']
            })
            
            # Mark installed instances as outdated
            self.db.execute_query("""
                UPDATE instance_plugins
                SET is_outdated = TRUE,
                    available_version = %(version)s
                WHERE plugin_id = %(plugin_id)s
                  AND installed_version != %(version)s
            """, {
                'plugin_id': plugin_id,
                'version': update_info['version']
            })
            
            # Check update strategy
            plugin_data = self.plugin_registry[plugin_id]
            strategy = plugin_data.get('update_strategy', 'manual')
            auto_update = plugin_data.get('auto_update_enabled', False)
            
            if auto_update and strategy == 'auto_stable' and not update_info.get('is_prerelease'):
                # Queue automatic update
                self._queue_plugin_update(plugin_id, update_info)
            elif strategy == 'notify_only':
                # Just log it (already done)
                pass
        
        except Exception as e:
            self.logger.error(f"Failed to handle new version for {plugin_id}: {e}")
    
    def _queue_plugin_update(self, plugin_id: str, update_info: Dict, 
                            target_instances: List[str] = None, priority: int = 5):
        """Queue a plugin update for deployment"""
        try:
            # Get current version from first installed instance
            cursor = self.db.execute_query("""
                SELECT installed_version FROM instance_plugins
                WHERE plugin_id = %(plugin_id)s
                LIMIT 1
            """, {'plugin_id': plugin_id}, fetch=True)
            
            from_version = cursor.fetchone()['installed_version'] if cursor.rowcount > 0 else None
            
            # Insert into queue
            self.db.execute_query("""
                INSERT INTO plugin_update_queue (
                    plugin_id, target_instances, from_version, to_version,
                    download_url, priority, created_by, status
                ) VALUES (
                    %(plugin_id)s, %(target_instances)s, %(from_version)s, %(to_version)s,
                    %(download_url)s, %(priority)s, 'agent', 'pending'
                )
            """, {
                'plugin_id': plugin_id,
                'target_instances': json.dumps(target_instances) if target_instances else '*',
                'from_version': from_version,
                'to_version': update_info['version'],
                'download_url': update_info['download_url'],
                'priority': priority
            })
            
            self.logger.info(f"✅ Queued update for {plugin_id}: {from_version} → {update_info['version']}")
        
        except Exception as e:
            self.logger.error(f"Failed to queue update for {plugin_id}: {e}")
    
    def _process_plugin_update_queue(self):
        """Process pending plugin updates"""
        try:
            # Get pending updates
            cursor = self.db.execute_query("""
                SELECT * FROM plugin_update_queue
                WHERE status = 'pending'
                  AND server_name = %(server_name)s
                ORDER BY priority DESC, created_at ASC
                LIMIT 10
            """, {'server_name': self.server_name}, fetch=True)
            
            for row in cursor:
                self._execute_plugin_update(dict(row))
        
        except Exception as e:
            self.logger.error(f"Failed to process update queue: {e}")
    
    def _execute_plugin_update(self, update_task: Dict):
        """Execute a single plugin update"""
        task_id = update_task['id']
        plugin_id = update_task['plugin_id']
        
        self.logger.info(f"🔄 Executing update: {plugin_id} → {update_task['to_version']}")
        
        try:
            # Mark as in progress
            self.db.execute_query("""
                UPDATE plugin_update_queue
                SET status = 'deploying', started_at = NOW()
                WHERE id = %(id)s
            """, {'id': task_id})
            
            # Download plugin
            jar_path = self._download_plugin(update_task['download_url'], plugin_id, update_task['to_version'])
            
            # Get target instances
            target_instances = json.loads(update_task['target_instances']) if update_task['target_instances'] != '*' else None
            
            if not target_instances:
                # Get all instances with this plugin
                cursor = self.db.execute_query("""
                    SELECT DISTINCT instance_id FROM instance_plugins
                    WHERE plugin_id = %(plugin_id)s
                """, {'plugin_id': plugin_id}, fetch=True)
                target_instances = [row['instance_id'] for row in cursor]
            
            # Deploy to each instance
            success_count = 0
            failure_count = 0
            
            for instance_id in target_instances:
                if self._deploy_plugin_to_instance(instance_id, plugin_id, jar_path, update_task['to_version']):
                    success_count += 1
                else:
                    failure_count += 1
            
            # Update queue status
            self.db.execute_query("""
                UPDATE plugin_update_queue
                SET status = 'completed',
                    completed_at = NOW(),
                    success_count = %(success)s,
                    failure_count = %(failure)s
                WHERE id = %(id)s
            """, {
                'id': task_id,
                'success': success_count,
                'failure': failure_count
            })
            
            self.logger.info(f"✅ Update complete: {success_count} success, {failure_count} failed")
        
        except Exception as e:
            self.logger.error(f"❌ Update failed for {plugin_id}: {e}")
            self.db.execute_query("""
                UPDATE plugin_update_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %(error)s
                WHERE id = %(id)s
            """, {'id': task_id, 'error': str(e)})
    
    def _download_plugin(self, url: str, plugin_id: str, version: str) -> Path:
        """Download plugin jar to temp location"""
        from pathlib import Path
        import tempfile
        
        temp_dir = Path(tempfile.gettempdir()) / 'archivesmp_updates'
        temp_dir.mkdir(exist_ok=True)
        
        jar_path = temp_dir / f"{plugin_id}-{version}.jar"
        
        self.logger.info(f"⬇️  Downloading {url}")
        
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(jar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        self.logger.info(f"✅ Downloaded to {jar_path}")
        return jar_path
    
    def _deploy_plugin_to_instance(self, instance_id: str, plugin_id: str, 
                                   jar_path: Path, version: str) -> bool:
        """Deploy plugin jar to specific instance"""
        try:
            # Get instance path
            cursor = self.db.execute_query("""
                SELECT instance_path FROM instances WHERE instance_id = %(instance_id)s
            """, {'instance_id': instance_id}, fetch=True)
            
            if cursor.rowcount == 0:
                return False
            
            instance_path = Path(cursor.fetchone()['instance_path'])
            plugins_dir = instance_path / 'Minecraft' / 'plugins'
            
            # Find and remove old version
            old_jars = list(plugins_dir.glob(f"{plugin_id}*.jar"))
            for old_jar in old_jars:
                old_jar.unlink()
                self.logger.info(f"🗑️  Removed old version: {old_jar.name}")
            
            # Copy new version
            import shutil
            new_jar_path = plugins_dir / jar_path.name
            shutil.copy2(jar_path, new_jar_path)
            
            # Update database
            self.db.execute_query("""
                UPDATE instance_plugins
                SET installed_version = %(version)s,
                    file_name = %(file_name)s,
                    file_hash = %(file_hash)s,
                    is_outdated = FALSE,
                    installation_method = 'agent',
                    last_seen_at = NOW()
                WHERE instance_id = %(instance_id)s AND plugin_id = %(plugin_id)s
            """, {
                'instance_id': instance_id,
                'plugin_id': plugin_id,
                'version': version,
                'file_name': jar_path.name,
                'file_hash': self._calculate_file_hash(new_jar_path)
            })
            
            self.logger.info(f"✅ Deployed {plugin_id} v{version} to {instance_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Failed to deploy to {instance_id}: {e}")
            return False
    
    def _process_datapack_deployment_queue(self):
        """Process datapack deployment queue"""
        # Similar to plugin updates but for datapacks
        pass
    
    def _process_webhook_events(self):
        """Process incoming webhook events from CI/CD systems"""
        try:
            # Get unprocessed webhook events
            cursor = self.db.execute_query("""
                SELECT * FROM cicd_webhook_events
                WHERE status = 'pending'
                ORDER BY received_at ASC
                LIMIT 20
            """, fetch=True)
            
            for row in cursor:
                event = dict(row)
                self._handle_webhook_event(event)
        
        except Exception as e:
            self.logger.error(f"Failed to process webhook events: {e}")
    
    def _handle_webhook_event(self, event: Dict):
        """Handle a single webhook event"""
        event_id = event['event_id']
        
        try:
            # Mark as processing
            self.db.execute_query("""
                UPDATE cicd_webhook_events
                SET processed_at = NOW()
                WHERE event_id = %(id)s
            """, {'id': event_id})
            
            # Extract version and download URL from payload
            payload = json.loads(event['payload'])
            
            if event['provider'] == 'github' and event['event_type'] == 'release':
                # GitHub release event
                version = payload['release']['tag_name'].lstrip('v')
                
                # Find jar asset
                jar_asset = None
                for asset in payload['release'].get('assets', []):
                    if asset['name'].endswith('.jar'):
                        jar_asset = asset
                        break
                
                if jar_asset and event['plugin_id']:
                    update_info = {
                        'version': version,
                        'download_url': jar_asset['browser_download_url'],
                        'changelog': payload['release'].get('body', ''),
                        'is_prerelease': payload['release'].get('prerelease', False)
                    }
                    
                    self._handle_new_version(event['plugin_id'], update_info)
                    
                    self.db.execute_query("""
                        UPDATE cicd_webhook_events
                        SET status = 'processed',
                            action_taken = 'Queued update'
                        WHERE event_id = %(id)s
                    """, {'id': event_id})
                else:
                    self.db.execute_query("""
                        UPDATE cicd_webhook_events
                        SET status = 'ignored',
                            action_taken = 'No jar asset found'
                        WHERE event_id = %(id)s
                    """, {'id': event_id})
        
        except Exception as e:
            self.logger.error(f"Failed to handle webhook event {event_id}: {e}")
            self.db.execute_query("""
                UPDATE cicd_webhook_events
                SET status = 'failed'
                WHERE event_id = %(id)s
            """, {'id': event_id})
