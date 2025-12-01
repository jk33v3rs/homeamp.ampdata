"""
Excel Reader Module

Reads configuration data from Excel files:
- deployment_matrix.csv: Which plugins to auto-update per server
- Master_Variable_Configurations.xlsx: Server-specific variable values
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class ExcelConfigReader:
    """Read configuration data from Excel/CSV files"""
    
    def __init__(self, data_dir: Path):
        """
        Initialize Excel reader
        
        Args:
            data_dir: Path to reference_data directory
        """
        self.data_dir = Path(data_dir)
        self.deployment_matrix_path = self.data_dir / "deployment_matrix.csv"
        self.variables_path = self.data_dir / "Master_Variable_Configurations.xlsx"
        self.logger = logging.getLogger(__name__)
        
        # Cache for loaded data
        self._deployment_matrix = None
        self._server_variables = None
    
    def load_deployment_matrix(self) -> pd.DataFrame:
        """
        Load deployment matrix from CSV
        
        Returns:
            DataFrame with columns: plugin_name, auto_update, dev01, prod01, etc.
        """
        try:
            if self._deployment_matrix is None:
                if not self.deployment_matrix_path.exists():
                    self.logger.error(f"Deployment matrix not found: {self.deployment_matrix_path}")
                    return pd.DataFrame()
                
                self._deployment_matrix = pd.read_csv(self.deployment_matrix_path)
                self.logger.info(f"Loaded deployment matrix: {len(self._deployment_matrix)} plugins")
            
            return self._deployment_matrix
            
        except Exception as e:
            self.logger.error(f"Error loading deployment matrix: {e}")
            return pd.DataFrame()
    
    def load_server_variables(self) -> Dict[str, Dict[str, Any]]:
        """
        Load server-specific variables from Master_Variable_Configurations.xlsx
        
        Returns:
            Dict mapping server_name -> {variable_name: value}
            Example:
            {
                'DEV01': {'max_players': 20, 'world_name': 'world_dev', ...},
                'PROD01': {'max_players': 100, 'world_name': 'world', ...}
            }
        """
        try:
            if self._server_variables is None:
                if not self.variables_path.exists():
                    self.logger.error(f"Variables file not found: {self.variables_path}")
                    return {}
                
                # Read all sheets (each sheet might be a different config aspect)
                excel_file = pd.ExcelFile(self.variables_path)
                server_vars = {}
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Expected format: First column is variable name, rest are server columns
                    if len(df.columns) < 2:
                        continue
                    
                    variable_col = df.columns[0]  # Usually 'Variable' or 'Setting'
                    
                    # Each column after first is a server name
                    for col in df.columns[1:]:
                        server_name = str(col).strip()
                        
                        if server_name not in server_vars:
                            server_vars[server_name] = {}
                        
                        # Map variable names to values for this server
                        for idx, row in df.iterrows():
                            var_name = str(row[variable_col]).strip()
                            var_value = row[col]
                            
                            # Skip empty values
                            if pd.isna(var_value) or var_value == '':
                                continue
                            
                            server_vars[server_name][var_name] = var_value
                
                self._server_variables = server_vars
                self.logger.info(f"Loaded variables for {len(server_vars)} servers")
            
            return self._server_variables
            
        except Exception as e:
            self.logger.error(f"Error loading server variables: {e}")
            return {}
    
    def get_server_variables(self, server_name: str) -> Dict[str, Any]:
        """
        Get variables for a specific server
        
        Args:
            server_name: Name of server (e.g., 'DEV01', 'PROD01')
            
        Returns:
            Dict of variable_name -> value
        """
        all_vars = self.load_server_variables()
        return all_vars.get(server_name, {})
    
    def get_plugin_auto_update_status(self, plugin_name: str) -> bool:
        """
        Check if a plugin should be auto-updated
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            True if auto_update is enabled
        """
        matrix = self.load_deployment_matrix()
        
        if matrix.empty:
            return False
        
        # Find plugin row
        plugin_row = matrix[matrix['plugin_name'].str.lower() == plugin_name.lower()]
        
        if plugin_row.empty:
            return False
        
        # Check auto_update column
        if 'auto_update' in plugin_row.columns:
            auto_update = plugin_row.iloc[0]['auto_update']
            
            # Handle various boolean representations
            if isinstance(auto_update, bool):
                return auto_update
            if isinstance(auto_update, str):
                return auto_update.lower() in ['true', 'yes', '1', 'enabled']
            if isinstance(auto_update, (int, float)):
                return bool(auto_update)
        
        return False
    
    def get_plugin_deployment_servers(self, plugin_name: str) -> List[str]:
        """
        Get list of servers where a plugin should be deployed
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of server names where plugin is marked for deployment
        """
        matrix = self.load_deployment_matrix()
        
        if matrix.empty:
            return []
        
        # Find plugin row
        plugin_row = matrix[matrix['plugin_name'].str.lower() == plugin_name.lower()]
        
        if plugin_row.empty:
            return []
        
        servers = []
        row = plugin_row.iloc[0]
        
        # Check each column (skip plugin_name and auto_update)
        skip_cols = ['plugin_name', 'auto_update', 'version', 'source']
        
        for col in matrix.columns:
            if col in skip_cols:
                continue
            
            # If column value is truthy, it's a deployment target
            value = row[col]
            if pd.notna(value) and value:
                # Handle boolean or string values
                if isinstance(value, bool) and value:
                    servers.append(col)
                elif isinstance(value, str) and value.lower() in ['true', 'yes', '1', 'x']:
                    servers.append(col)
                elif isinstance(value, (int, float)) and value:
                    servers.append(col)
        
        return servers
    
    def write_plugin_update(self, plugin_name: str, new_version: str, 
                           update_date: str = None) -> bool:
        """
        Update plugin version in deployment matrix
        
        Args:
            plugin_name: Name of plugin
            new_version: New version to record
            update_date: Date of update (default: now)
            
        Returns:
            True if successful
        """
        try:
            matrix = self.load_deployment_matrix()
            
            if matrix.empty:
                self.logger.error("Cannot update empty deployment matrix")
                return False
            
            # Find plugin row
            mask = matrix['plugin_name'].str.lower() == plugin_name.lower()
            
            if not mask.any():
                self.logger.warning(f"Plugin {plugin_name} not found in matrix")
                return False
            
            # Update version
            if 'version' in matrix.columns:
                matrix.loc[mask, 'version'] = new_version
            
            # Update last_updated if column exists
            if 'last_updated' in matrix.columns:
                matrix.loc[mask, 'last_updated'] = update_date or datetime.now().strftime('%Y-%m-%d')
            
            # Write back to CSV
            matrix.to_csv(self.deployment_matrix_path, index=False)
            
            # Invalidate cache
            self._deployment_matrix = None
            
            self.logger.info(f"Updated {plugin_name} to version {new_version} in matrix")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating deployment matrix: {e}")
            return False
    
    def get_all_plugins_for_server(self, server_name: str) -> List[str]:
        """
        Get all plugins deployed on a specific server
        
        Args:
            server_name: Name of server
            
        Returns:
            List of plugin names
        """
        matrix = self.load_deployment_matrix()
        
        if matrix.empty or server_name not in matrix.columns:
            return []
        
        plugins = []
        
        for idx, row in matrix.iterrows():
            if pd.notna(row[server_name]) and row[server_name]:
                plugin_name = row['plugin_name']
                if pd.notna(plugin_name):
                    plugins.append(str(plugin_name))
        
        return plugins
