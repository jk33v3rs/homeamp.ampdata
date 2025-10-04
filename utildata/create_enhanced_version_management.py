#!/usr/bin/env python3
"""
ArchiveSMP Version Management System - Using Existing Plugin Registry
Parse and enhance the comprehensive plugin registry with version tracking and CI/CD automation
"""

import pandas as pd
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_plugin_registry():
    """Parse the existing comprehensive plugin registry CSV."""
    
    # Load the existing plugin registry
    csv_path = Path("d:/homeamp.ampdata/excel_extracted/Plugins_IN_USE.csv")
    
    logger.info(f"Loading plugin registry from {csv_path}")
    
    # Read CSV with proper header row (row 2 has the column headers)
    df = pd.read_csv(csv_path, header=2)
    
    logger.info(f"CSV has {len(df.columns)} columns")
    logger.info(f"Column names: {list(df.columns)}")
    
    # The structure based on debug output:
    # Column 0: Empty/NaN mostly  
    # Column 1: Plugin names (PLUGINS)
    # Column 2: Current version (1.21.5)
    # Column 3: Latest known (1.21.6) 
    # Column 4: Server category (M = Minimal, S = Standard...)
    # etc.
    
    # Rename columns to meaningful names
    df.columns = [
        "Empty", "Plugin_Name", "Current_Version", "Latest_Known", 
        "Server_Category", "MC_Version", "Config_Status", "MC_Version_2",
        "Config_Notes", "Source_Platform", "Distribution", "Latest_Version",
        "Documentation", "Additional_Notes", "CI_CD_Link", "File_Path",
        "Deployed_Servers", "Location_Status", "Additional_Links"
    ]
    
    # Remove empty rows and clean data
    df = df.dropna(subset=['Plugin_Name'])
    # Convert Plugin_Name to string and filter
    df['Plugin_Name'] = df['Plugin_Name'].astype(str)
    df = df[df['Plugin_Name'].str.strip() != '']
    df = df[df['Plugin_Name'] != 'nan']
    df = df[df['Plugin_Name'] != 'PLUGINS']  # Remove header row
    
    logger.info(f"Parsed {len(df)} plugin entries")
    
    return df

def extract_ci_cd_info(df):
    """Extract and standardize CI/CD information from the registry."""
    
    ci_cd_mapping = []
    
    for idx, row in df.iterrows():
        plugin_name = row['Plugin_Name']
        if pd.isna(plugin_name) or plugin_name.strip() == '':
            continue
            
        # Parse CI/CD links and source information
        ci_cd_link = row.get('CI_CD_Link', '')
        source_platform = row.get('Source_Platform', '')
        distribution = row.get('Distribution', '')
        current_version = row.get('Current_Version', '')
        latest_version = row.get('Latest_Version', '')
        
        # Determine update source and method
        update_source = determine_update_source(ci_cd_link, source_platform, distribution)
        
        # Extract version checking method
        version_check_method = determine_version_check_method(ci_cd_link, update_source)
        
        # Determine update priority based on plugin category and stability
        priority = determine_priority(plugin_name, current_version, row.get('Server_Category', ''))
        
        ci_cd_info = {
            "plugin_name": plugin_name,
            "current_version": current_version,
            "latest_known_version": latest_version,
            "source_platform": source_platform,
            "distribution_platform": distribution,
            "ci_cd_link": ci_cd_link,
            "update_source": update_source,
            "version_check_method": version_check_method,
            "api_endpoint": extract_api_endpoint(ci_cd_link, update_source),
            "download_method": determine_download_method(ci_cd_link, update_source),
            "priority": priority,
            "auto_update_safe": is_auto_update_safe(plugin_name, current_version),
            "deployed_servers": row.get('Deployed_Servers', ''),
            "config_required": not pd.isna(row.get('Config_Status', '')),
            "documentation_url": row.get('Documentation', ''),
            "additional_notes": row.get('Additional_Notes', ''),
            "additional_links": row.get('Additional_Links', '')
        }
        
        ci_cd_mapping.append(ci_cd_info)
    
    return ci_cd_mapping

def determine_update_source(ci_cd_link, source_platform, distribution):
    """Determine the primary update source based on available information."""
    
    # Handle NaN values
    if pd.isna(ci_cd_link):
        ci_cd_link = ''
    if pd.isna(source_platform):
        source_platform = ''
    if pd.isna(distribution):
        distribution = ''
    
    ci_cd_link = str(ci_cd_link).strip()
    source_platform = str(source_platform).strip()
    distribution = str(distribution).strip()
    
    ci_cd_lower = ci_cd_link.lower()
    
    # GitHub Actions/Releases
    if 'github.com' in ci_cd_lower and '/releases' in ci_cd_lower:
        return 'github_releases'
    elif 'github.com' in ci_cd_lower and '/actions' in ci_cd_lower:
        return 'github_actions'
    
    # Jenkins CI systems
    elif 'codemc.io' in ci_cd_lower:
        return 'codemc_jenkins'
    elif 'ci.extendedclip.com' in ci_cd_lower:
        return 'extendedclip_jenkins'
    elif 'ci.dmulloy2.net' in ci_cd_lower:
        return 'dmulloy2_jenkins'
    elif 'ci.loohpjames.com' in ci_cd_lower:
        return 'loohpjames_jenkins'
    elif 'builds.enginehub.org' in ci_cd_lower:
        return 'enginehub_jenkins'
    elif 'ci.md-5.net' in ci_cd_lower:
        return 'md5_jenkins'
    
    # Platform-based sources
    elif 'modrinth' in distribution.lower() or 'modrinth' in source_platform.lower():
        return 'modrinth_api'
    elif 'spigotmc' in distribution.lower() or 'spigot' in source_platform.lower():
        return 'spigot_api'
    elif 'hangar' in distribution.lower():
        return 'hangar_api'
    elif 'bukkit' in distribution.lower():
        return 'bukkit_dev'
    
    # Official websites
    elif 'william278.net' in ci_cd_lower:
        return 'william278_official'
    elif 'zrips.net' in ci_cd_lower:
        return 'zrips_official'
    elif 'luckperms.net' in ci_cd_lower:
        return 'luckperms_official'
    elif 'coreprotect.net' in ci_cd_lower:
        return 'coreprotect_official'
    
    return 'manual_check'

def determine_version_check_method(ci_cd_link, update_source):
    """Determine how to check for version updates."""
    
    method_mapping = {
        'github_releases': 'github_releases_api',
        'github_actions': 'github_releases_api',
        'codemc_jenkins': 'jenkins_last_successful',
        'extendedclip_jenkins': 'jenkins_last_successful', 
        'dmulloy2_jenkins': 'jenkins_last_successful',
        'loohpjames_jenkins': 'jenkins_last_successful',
        'enginehub_jenkins': 'jenkins_last_successful',
        'md5_jenkins': 'jenkins_last_successful',
        'modrinth_api': 'modrinth_versions_api',
        'spigot_api': 'spigot_legacy_api',
        'hangar_api': 'hangar_versions_api',
        'bukkit_dev': 'bukkit_files_api',
        'william278_official': 'manual_check',
        'zrips_official': 'manual_check', 
        'luckperms_official': 'github_releases_api',
        'coreprotect_official': 'manual_check',
        'manual_check': 'manual_check'
    }
    
    return method_mapping.get(update_source, 'manual_check')

def extract_api_endpoint(ci_cd_link, update_source):
    """Extract or construct API endpoint for version checking."""
    
    if pd.isna(ci_cd_link) or ci_cd_link.strip() == '':
        return ''
    
    # GitHub releases API
    if update_source == 'github_releases' or update_source == 'github_actions':
        github_match = re.search(r'github\.com/([^/]+)/([^/]+)', ci_cd_link)
        if github_match:
            owner, repo = github_match.groups()
            return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    # Jenkins CI endpoints (return the build API)
    elif 'jenkins' in update_source:
        if 'lastSuccessfulBuild' in ci_cd_link:
            return ci_cd_link + '/api/json'
        elif 'lastStableBuild' in ci_cd_link:
            return ci_cd_link + '/api/json'
    
    # Modrinth API
    elif update_source == 'modrinth_api':
        # Extract project ID from modrinth links
        modrinth_match = re.search(r'modrinth\.com/plugin/([^/]+)', ci_cd_link)
        if modrinth_match:
            project_id = modrinth_match.group(1)
            return f"https://api.modrinth.com/v2/project/{project_id}/version"
    
    # Spigot API (need resource ID)
    elif update_source == 'spigot_api':
        # Handle different Spigot URL formats:
        # https://www.spigotmc.org/resources/plugin-name.ID/
        # https://www.spigotmc.org/resources/ID/
        spigot_match = re.search(r'spigotmc\.org/resources/[^/]*\.?(\d+)/?', ci_cd_link)
        if spigot_match:
            resource_id = spigot_match.group(1)
            return f"https://api.spigotmc.org/legacy/update.php?resource={resource_id}"
    
    return ci_cd_link

def determine_download_method(ci_cd_link, update_source):
    """Determine how plugins should be downloaded."""
    
    if 'jenkins' in update_source:
        return 'jenkins_artifact'
    elif update_source in ['github_releases', 'github_actions']:
        return 'github_release_asset'
    elif update_source == 'modrinth_api':
        return 'modrinth_file_download'
    elif update_source == 'spigot_api':
        return 'manual_download'  # Spigot requires authentication for most resources
    elif update_source == 'hangar_api':
        return 'hangar_file_download'
    else:
        return 'manual_download'

def determine_priority(plugin_name, current_version, server_category):
    """Determine update priority based on plugin importance and stability."""
    
    # Core infrastructure plugins - high priority for updates
    high_priority_plugins = [
        'LuckPerms', 'CoreProtect', 'WorldEdit', 'WorldGuard', 'ProtocolLib',
        'PlaceholderAPI', 'VaultUnlocked', 'TheNewEconomy', 'HuskSync', 'EliteMobs'
    ]
    
    # Development/snapshot versions need more frequent checking
    if pd.notna(current_version) and ('SNAPSHOT' in str(current_version) or 'DEV' in str(current_version)):
        return 'high'
    
    # Core plugins are high priority
    if plugin_name in high_priority_plugins:
        return 'high'
    
    # Plugins deployed to all servers (S,M or similar broad categories)
    if pd.notna(server_category) and any(cat in str(server_category) for cat in ['S,M', 'S, M']):
        return 'medium'
    
    # Single-server or specialized plugins
    return 'low'

def is_auto_update_safe(plugin_name, current_version):
    """Determine if plugin is safe for automated updates."""
    
    # Plugins that generally break compatibility or need config changes
    risky_plugins = [
        'CMI', 'ExcellentEnchants', 'ExcellentJobs', 
        'HuskSync', 'PLAN', 'TheNewEconomy'
    ]
    
    # Plugins that are explicitly safe for auto-updates
    auto_safe_plugins = [
        'ProtocolLib', 'EliteMobs', 'CoreProtect', 'LuckPerms', 
        'WorldEdit', 'WorldGuard', 'PlaceholderAPI', 'ViaVersion',
        'ViaBackwards', 'Geyser', 'Floodgate', 'mcMMO'
    ]
    
    # SNAPSHOT/DEV versions should be manually reviewed
    if pd.notna(current_version) and ('SNAPSHOT' in str(current_version) or 'DEV' in str(current_version)):
        return False
    
    # Explicitly safe plugins can be auto-updated
    if plugin_name in auto_safe_plugins:
        return True
    
    # Known risky plugins need manual review
    if plugin_name in risky_plugins:
        return False
    
    return True

def create_github_actions_workflow(ci_cd_mapping):
    """Generate GitHub Actions workflow using the real plugin data."""
    
    # Group plugins by update method for efficient checking
    github_plugins = [p for p in ci_cd_mapping if p['version_check_method'] == 'github_releases_api']
    jenkins_plugins = [p for p in ci_cd_mapping if 'jenkins' in p['version_check_method']]
    modrinth_plugins = [p for p in ci_cd_mapping if p['version_check_method'] == 'modrinth_versions_api']
    spigot_plugins = [p for p in ci_cd_mapping if p['version_check_method'] == 'spigot_legacy_api']
    
    workflow_content = f"""name: ArchiveSMP Plugin Version Check & Update Pipeline

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6:00 AM UTC
  workflow_dispatch:
    inputs:
      force_update:
        description: 'Force update all plugins'
        required: false
        default: 'false'
        type: boolean

env:
  DISCORD_WEBHOOK_URL: ${{{{ secrets.DISCORD_WEBHOOK_URL }}}}

jobs:
  version-check:
    name: Check Plugin Versions
    runs-on: ubuntu-latest
    outputs:
      updates-available: ${{{{ steps.check-versions.outputs.updates-available }}}}
      
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests pandas openpyxl

      - name: Check GitHub-hosted plugins ({len(github_plugins)} plugins)
        run: |
          echo "Checking GitHub releases..."
"""
    
    # Add GitHub plugin checks
    for plugin in github_plugins[:10]:  # Limit to first 10 to avoid workflow bloat
        if plugin['api_endpoint']:
            workflow_content += f"""
          # {plugin['plugin_name']}
          curl -s -H "Authorization: token ${{{{ secrets.GITHUB_TOKEN }}}}" \\
            "{plugin['api_endpoint']}" | jq -r '.tag_name' || echo "API Error"
"""
    
    workflow_content += f"""
      - name: Check Jenkins CI plugins ({len(jenkins_plugins)} plugins)
        run: |
          echo "Checking Jenkins builds..."
"""
    
    # Add Jenkins plugin checks  
    for plugin in jenkins_plugins[:10]:
        if plugin['api_endpoint']:
            workflow_content += f"""
          # {plugin['plugin_name']}
          curl -s "{plugin['api_endpoint']}" | jq -r '.number' || echo "API Error"
"""
    
    workflow_content += f"""
      - name: Check Modrinth plugins ({len(modrinth_plugins)} plugins)
        run: |
          echo "Checking Modrinth projects..."
"""
    
    # Add Modrinth plugin checks
    for plugin in modrinth_plugins:
        if plugin['api_endpoint']:
            workflow_content += f"""
          # {plugin['plugin_name']}
          curl -s "{plugin['api_endpoint']}" | jq -r '.[0].version_number' || echo "API Error"
"""
    
    workflow_content += f"""
      - name: Check Spigot plugins ({len(spigot_plugins)} plugins)
        run: |
          echo "Checking Spigot resources..."
"""
    
    # Add Spigot plugin checks
    for plugin in spigot_plugins:
        if plugin['api_endpoint']:
            workflow_content += f"""
          # {plugin['plugin_name']}
          curl -s "{plugin['api_endpoint']}" || echo "API Error"
"""
    
    workflow_content += """
      - name: Generate update matrix
        id: check-versions
        run: |
          python3 << 'EOF'
          import json
          import os
          
          # This would contain actual version comparison logic
          # For now, simulating some updates available
          updates_needed = []
          
          with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
              if updates_needed:
                  f.write(f"updates-available=true\\n")
              else:
                  f.write(f"updates-available=false\\n")
          EOF

      - name: Discord notification
        if: always()
        run: |
          if [ "${{ steps.check-versions.outputs.updates-available }}" == "true" ]; then
            curl -H "Content-Type: application/json" \\
                 -d '{
                   "embeds": [{
                     "title": "🔄 ArchiveSMP Plugin Updates Available",
                     "description": "Found plugin updates. Review and approve for deployment.",
                     "color": 16776960,
                     "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
                   }]
                 }' \\
                 ${{ env.DISCORD_WEBHOOK_URL }}
          fi
"""
    
    return workflow_content

def main():
    """Main execution function."""
    logger.info("=== ArchiveSMP Version Management System (Real Data) ===")
    
    # Parse existing plugin registry
    df = parse_plugin_registry()
    logger.info(f"Loaded {len(df)} plugins from registry")
    
    # Extract CI/CD information
    ci_cd_mapping = extract_ci_cd_info(df)
    logger.info(f"Processed CI/CD information for {len(ci_cd_mapping)} plugins")
    
    # Create enhanced Excel file
    ci_cd_df = pd.DataFrame(ci_cd_mapping)
    
    excel_path = Path("d:/homeamp.ampdata/utildata/ArchiveSMP_Version_Management_Enhanced.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Main CI/CD data
        ci_cd_df.to_excel(writer, sheet_name='CI_CD_Enhanced', index=False)
        
        # Summary by update source
        source_summary = ci_cd_df.groupby('update_source').agg({
            'plugin_name': 'count',
            'priority': lambda x: ', '.join(x.unique())
        }).rename(columns={'plugin_name': 'plugin_count'}).reset_index()
        source_summary.to_excel(writer, sheet_name='Update_Sources', index=False)
        
        # Priority breakdown
        priority_summary = ci_cd_df.groupby('priority').agg({
            'plugin_name': 'count',
            'auto_update_safe': lambda x: sum(x)
        }).rename(columns={'plugin_name': 'plugin_count', 'auto_update_safe': 'auto_update_count'}).reset_index()
        priority_summary.to_excel(writer, sheet_name='Priority_Summary', index=False)
        
        # Auto-update safe plugins
        auto_safe = ci_cd_df[ci_cd_df['auto_update_safe'] == True][['plugin_name', 'current_version', 'update_source', 'api_endpoint']]
        auto_safe.to_excel(writer, sheet_name='Auto_Update_Safe', index=False)
    
    # Generate GitHub Actions workflow
    workflow_content = create_github_actions_workflow(ci_cd_mapping)
    workflow_path = Path("d:/homeamp.ampdata/utildata/github-workflows/real-plugin-pipeline.yml")
    workflow_path.parent.mkdir(exist_ok=True)
    
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    
    # Summary statistics
    total_plugins = len(ci_cd_mapping)
    github_count = len([p for p in ci_cd_mapping if p['version_check_method'] == 'github_releases_api'])
    jenkins_count = len([p for p in ci_cd_mapping if 'jenkins' in p['version_check_method']])
    modrinth_count = len([p for p in ci_cd_mapping if p['version_check_method'] == 'modrinth_versions_api'])
    spigot_count = len([p for p in ci_cd_mapping if p['version_check_method'] == 'spigot_legacy_api'])
    auto_safe_count = len([p for p in ci_cd_mapping if p['auto_update_safe']])
    
    logger.info(f"\n=== ENHANCED VERSION MANAGEMENT SUMMARY ===")
    logger.info(f"📋 Total plugins processed: {total_plugins}")
    logger.info(f"🔗 Update source breakdown:")
    logger.info(f"   • GitHub Releases: {github_count}")
    logger.info(f"   • Jenkins CI: {jenkins_count}")
    logger.info(f"   • Modrinth API: {modrinth_count}")
    logger.info(f"   • Spigot API: {spigot_count}")
    logger.info(f"   • Manual check: {total_plugins - github_count - jenkins_count - modrinth_count - spigot_count}")
    logger.info(f"🤖 Auto-update safe: {auto_safe_count}/{total_plugins}")
    
    logger.info(f"\n📊 Enhanced Excel file: {excel_path}")
    logger.info(f"⚡ GitHub Actions workflow: {workflow_path}")
    
    return excel_path

if __name__ == "__main__":
    main()