"""
Production Endpoint Agent - Part 3: CI/CD Integration & Update Management
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class AgentUpdateMethods:
    """Mixin class for plugin/datapack update management"""
    
    # ========================================================================
    # PLUGIN UPDATE CHECKING (CI/CD Integration)
    # ========================================================================
    
    def _check_plugin_updates(self):
        """
        Check for updates for all plugins via CI/CD APIs
        Supports: Modrinth, Hangar, GitHub Releases, SpigotMC
        """
        self.logger.info("[UPDATE] Checking for plugin updates")
        
        checked_count = 0
        updates_found = 0
        
        for plugin_id, plugin_info in self.plugin_registry.items():
            try:
                latest_version = None
                download_url = None
                
                # Try Modrinth API
                if plugin_info.get('modrinth_id'):
                    latest_version, download_url = self._check_modrinth_update(plugin_info['modrinth_id'])
                
                # Try GitHub Releases
                elif plugin_info.get('github_repo'):
                    latest_version, download_url = self._check_github_release(plugin_info['github_repo'])
                
                # Try Hangar API
                elif plugin_info.get('hangar_slug'):
                    latest_version, download_url = self._check_hangar_update(plugin_info['hangar_slug'])
                
                # Update registry if new version found
                if latest_version and latest_version != plugin_info.get('current_stable_version'):
                    self.logger.info(f"[NEW] Update available: {plugin_id} {plugin_info.get('current_stable_version')} → {latest_version}")
                    self._record_available_update(plugin_id, latest_version, download_url)
                    updates_found += 1
                
                checked_count += 1
            
            except Exception as e:
                self.logger.warning(f"[WARN]  Failed to check updates for {plugin_id}: {e}")
        
        self.logger.info(f"[OK] Update check complete: {checked_count} plugins checked, {updates_found} updates found")
    
    def _check_modrinth_update(self, modrinth_id: str) -> tuple[Optional[str], Optional[str]]:
        """Check Modrinth API for latest version"""
        try:
            # Get project versions
            response = requests.get(
                f"https://api.modrinth.com/v2/project/{modrinth_id}/version",
                headers={'User-Agent': 'ArchiveSMP-Config-Manager/1.0'}
            )
            
            if response.status_code != 200:
                return None, None
            
            versions = response.json()
            if not versions:
                return None, None
            
            # Get latest stable version
            latest = versions[0]  # Modrinth returns newest first
            version_number = latest['version_number']
            
            # Get primary download file
            files = latest.get('files', [])
            primary_file = next((f for f in files if f.get('primary')), files[0] if files else None)
            download_url = primary_file['url'] if primary_file else None
            
            return version_number, download_url
        
        except Exception as e:
            self.logger.debug(f"Modrinth check failed for {modrinth_id}: {e}")
            return None, None
    
    def _check_github_release(self, github_repo: str) -> tuple[Optional[str], Optional[str]]:
        """Check GitHub Releases API for latest version"""
        try:
            # Get latest release
            response = requests.get(
                f"https://api.github.com/repos/{github_repo}/releases/latest",
                headers={'User-Agent': 'ArchiveSMP-Config-Manager/1.0'}
            )
            
            if response.status_code != 200:
                return None, None
            
            release = response.json()
            version = release['tag_name'].lstrip('v')  # Remove 'v' prefix if present
            
            # Get first jar asset
            assets = release.get('assets', [])
            jar_asset = next((a for a in assets if a['name'].endswith('.jar')), None)
            download_url = jar_asset['browser_download_url'] if jar_asset else None
            
            return version, download_url
        
        except Exception as e:
            self.logger.debug(f"GitHub check failed for {github_repo}: {e}")
            return None, None
    
    def _check_hangar_update(self, hangar_slug: str) -> tuple[Optional[str], Optional[str]]:
        """Check Hangar API for latest version"""
        try:
            # Get project versions
            response = requests.get(
                f"https://hangar.papermc.io/api/v1/projects/{hangar_slug}/versions",
                headers={'User-Agent': 'ArchiveSMP-Config-Manager/1.0'}
            )
            
            if response.status_code != 200:
                return None, None
            
            data = response.json()
            versions = data.get('result', [])
            if not versions:
                return None, None
            
            latest = versions[0]
            version_number = latest['name']
            
            # Construct download URL
            download_url = f"https://hangar.papermc.io/api/v1/projects/{hangar_slug}/versions/{version_number}/download"
            
            return version_number, download_url
        
        except Exception as e:
            self.logger.debug(f"Hangar check failed for {hangar_slug}: {e}")
            return None, None
    
    def _record_available_update(self, plugin_id: str, latest_version: str, download_url: str):
        """Record available update in database"""
        try:
            # Update plugin registry
            self.db.execute_query("""
                UPDATE plugins
                SET latest_version = %(latest_version)s,
                    last_update_check_at = NOW(),
                    last_available_version_at = NOW()
                WHERE plugin_id = %(plugin_id)s
            """, {
                'plugin_id': plugin_id,
                'latest_version': latest_version
            })
            
            # Mark installed instances as outdated
            self.db.execute_query("""
                UPDATE instance_plugins
                SET is_outdated = TRUE,
                    available_version = %(latest_version)s
                WHERE plugin_id = %(plugin_id)s
                  AND installed_version != %(latest_version)s
            """, {
                'plugin_id': plugin_id,
                'latest_version': latest_version
            })
            
            # Check if auto-update enabled
            plugin = self.plugin_registry.get(plugin_id, {})
            if plugin.get('auto_update_enabled') and plugin.get('update_strategy') in ['auto_stable', 'auto_latest']:
                self._queue_plugin_update(plugin_id, latest_version, download_url, auto=True)
        
        except Exception as e:
            self.logger.error(f"Failed to record update for {plugin_id}: {e}")
    
    def _queue_plugin_update(self, plugin_id: str, to_version: str, download_url: str, auto: bool = False):
        """Add plugin update to deployment queue"""
        try:
            # Get all instances with this plugin
            cursor = self.db.execute_query("""
                SELECT instance_id FROM instance_plugins
                WHERE plugin_id = %(plugin_id)s
            """, {'plugin_id': plugin_id}, fetch=True)
            
            instance_ids = [row['instance_id'] for row in cursor]
            
            if not instance_ids:
                return
            
            # Queue update
            self.db.execute_query("""
                INSERT INTO plugin_update_queue (
                    plugin_id, target_instances, to_version, download_url,
                    priority, status, created_by, created_at
                ) VALUES (
                    %(plugin_id)s, %(target_instances)s, %(to_version)s, %(download_url)s,
                    %(priority)s, 'pending', %(created_by)s, NOW()
                )
            """, {
                'plugin_id': plugin_id,
                'target_instances': json.dumps(instance_ids),
                'to_version': to_version,
                'download_url': download_url,
                'priority': 8 if auto else 5,
                'created_by': f'agent-{self.server_name}' if auto else 'user'
            })
            
            self.logger.info(f" Queued update for {plugin_id} → {to_version} ({len(instance_ids)} instances)")
        
        except Exception as e:
            self.logger.error(f"Failed to queue update for {plugin_id}: {e}")
    
    # ========================================================================
    # UPDATE QUEUE PROCESSING
    # ========================================================================
    
    def _process_plugin_update_queue(self):
        """Process pending plugin updates"""
        try:
            # Get pending updates
            cursor = self.db.execute_query("""
                SELECT * FROM plugin_update_queue
                WHERE status = 'pending'
                  AND (scheduled_for IS NULL OR scheduled_for <= NOW())
                ORDER BY priority DESC, created_at ASC
                LIMIT 5
            """, fetch=True)
            
            for update in cursor:
                self._execute_plugin_update(update)
        
        except Exception as e:
            self.logger.error(f"Failed to process plugin update queue: {e}")
    
    def _execute_plugin_update(self, update: Dict):
        """Execute a single plugin update"""
        update_id = update['id']
        plugin_id = update['plugin_id']
        to_version = update['to_version']
        download_url = update['download_url']
        target_instances = json.loads(update['target_instances'])
        
        self.logger.info(f"[UPDATE] Executing update: {plugin_id} → {to_version}")
        
        # Mark as in progress
        self.db.execute_query("""
            UPDATE plugin_update_queue
            SET status = 'deploying', started_at = NOW()
            WHERE id = %(id)s
        """, {'id': update_id})
        
        success_count = 0
        failure_count = 0
        deployment_log = []
        
        try:
            # Download plugin jar
            jar_data = self._download_plugin(download_url)
            if not jar_data:
                raise Exception(f"Failed to download from {download_url}")
            
            # Deploy to each instance
            for instance_id in target_instances:
                try:
                    instance_path = self._get_instance_path(instance_id)
                    if not instance_path:
                        raise Exception(f"Instance path not found: {instance_id}")
                    
                    # Get current plugin jar name
                    cursor = self.db.execute_query("""
                        SELECT file_name FROM instance_plugins
                        WHERE instance_id = %(instance_id)s AND plugin_id = %(plugin_id)s
                    """, {'instance_id': instance_id, 'plugin_id': plugin_id}, fetch=True)
                    
                    if cursor.rowcount == 0:
                        deployment_log.append(f"[ERROR] {instance_id}: Plugin not installed")
                        failure_count += 1
                        continue
                    
                    old_jar_name = cursor.fetchone()['file_name']
                    
                    # Write new jar
                    plugins_dir = Path(instance_path) / 'Minecraft' / 'plugins'
                    new_jar_path = plugins_dir / old_jar_name  # Keep same name
                    
                    # Backup old jar
                    if new_jar_path.exists():
                        backup_path = plugins_dir / f"{old_jar_name}.backup"
                        new_jar_path.rename(backup_path)
                    
                    # Write new jar
                    with open(new_jar_path, 'wb') as f:
                        f.write(jar_data)
                    
                    # Update database
                    file_hash = hashlib.sha256(jar_data).hexdigest()
                    self.db.execute_query("""
                        UPDATE instance_plugins
                        SET installed_version = %(version)s,
                            file_hash = %(file_hash)s,
                            is_outdated = FALSE,
                            last_seen_at = NOW()
                        WHERE instance_id = %(instance_id)s AND plugin_id = %(plugin_id)s
                    """, {
                        'instance_id': instance_id,
                        'plugin_id': plugin_id,
                        'version': to_version,
                        'file_hash': file_hash
                    })
                    
                    deployment_log.append(f"[OK] {instance_id}: Updated successfully")
                    success_count += 1
                
                except Exception as e:
                    deployment_log.append(f"[ERROR] {instance_id}: {str(e)}")
                    failure_count += 1
                    self.logger.error(f"Failed to update {plugin_id} on {instance_id}: {e}")
            
            # Mark as completed
            self.db.execute_query("""
                UPDATE plugin_update_queue
                SET status = 'completed',
                    completed_at = NOW(),
                    success_count = %(success_count)s,
                    failure_count = %(failure_count)s,
                    deployment_log = %(deployment_log)s
                WHERE id = %(id)s
            """, {
                'id': update_id,
                'success_count': success_count,
                'failure_count': failure_count,
                'deployment_log': '\n'.join(deployment_log)
            })
            
            self.logger.info(f"[OK] Update complete: {success_count} succeeded, {failure_count} failed")
        
        except Exception as e:
            # Mark as failed
            self.db.execute_query("""
                UPDATE plugin_update_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %(error)s
                WHERE id = %(id)s
            """, {
                'id': update_id,
                'error': str(e)
            })
            
            self.logger.error(f"[ERROR] Update failed: {e}")
    
    def _download_plugin(self, url: str) -> Optional[bytes]:
        """Download plugin jar from URL"""
        try:
            response = requests.get(url, timeout=30, headers={'User-Agent': 'ArchiveSMP-Config-Manager/1.0'})
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None
    
    def _get_instance_path(self, instance_id: str) -> Optional[str]:
        """Get instance filesystem path from database"""
        try:
            cursor = self.db.execute_query("""
                SELECT instance_id FROM instances WHERE instance_id = %(instance_id)s
            """, {'instance_id': instance_id}, fetch=True)
            
            if cursor.rowcount == 0:
                return None
            
            return str(self.amp_base_dir / instance_id)
        except:
            return None
    
    # ========================================================================
    # DATAPACK DEPLOYMENT
    # ========================================================================
    
    def _process_datapack_deployment_queue(self):
        """Process pending datapack deployments"""
        try:
            cursor = self.db.execute_query("""
                SELECT * FROM datapack_deployment_queue
                WHERE status = 'pending'
                  AND (scheduled_for IS NULL OR scheduled_for <= NOW())
                ORDER BY priority DESC, created_at ASC
                LIMIT 5
            """, fetch=True)
            
            for deployment in cursor:
                self._execute_datapack_deployment(deployment)
        
        except Exception as e:
            self.logger.error(f"Failed to process datapack queue: {e}")
    
    def _execute_datapack_deployment(self, deployment: Dict):
        """Execute datapack installation/update/removal"""
        # Similar to plugin update but for datapacks
        # Handles world/datapacks folder, not plugins/
        pass  # Implementation similar to _execute_plugin_update
    
    # ========================================================================
    # WEBHOOK EVENT PROCESSING
    # ========================================================================
    
    def _process_webhook_events(self):
        """Process incoming CI/CD webhook events"""
        try:
            cursor = self.db.execute_query("""
                SELECT * FROM cicd_webhook_events
                WHERE status = 'pending'
                ORDER BY received_at ASC
                LIMIT 10
            """, fetch=True)
            
            for event in cursor:
                self._handle_webhook_event(event)
        
        except Exception as e:
            self.logger.error(f"Failed to process webhook events: {e}")
    
    def _handle_webhook_event(self, event: Dict):
        """Handle a single webhook event"""
        event_id = event['event_id']
        plugin_id = event['plugin_id']
        provider = event['provider']
        version = event['version']
        download_url = event['download_url']
        is_prerelease = event['is_prerelease']
        
        try:
            self.logger.info(f" Processing webhook: {provider} {plugin_id} {version}")
            
            # Get plugin auto-update settings
            plugin = self.plugin_registry.get(plugin_id)
            if not plugin:
                action_taken = "Ignored: Plugin not in registry"
            elif is_prerelease and plugin.get('update_strategy') == 'auto_stable':
                action_taken = "Ignored: Prerelease (auto_stable only)"
            elif plugin.get('auto_update_enabled'):
                # Queue update
                self._queue_plugin_update(plugin_id, version, download_url, auto=True)
                action_taken = f"Queued auto-update to {version}"
            else:
                # Just record available version
                self._record_available_update(plugin_id, version, download_url)
                action_taken = f"Recorded new version {version}"
            
            # Mark event as processed
            self.db.execute_query("""
                UPDATE cicd_webhook_events
                SET status = 'processed',
                    processed_at = NOW(),
                    action_taken = %(action)s
                WHERE event_id = %(event_id)s
            """, {
                'event_id': event_id,
                'action': action_taken
            })
            
            self.logger.info(f"[OK] Webhook processed: {action_taken}")
        
        except Exception as e:
            self.db.execute_query("""
                UPDATE cicd_webhook_events
                SET status = 'failed', processed_at = NOW()
                WHERE event_id = %(event_id)s
            """, {'event_id': event_id})
            
            self.logger.error(f"Failed to process webhook {event_id}: {e}")
