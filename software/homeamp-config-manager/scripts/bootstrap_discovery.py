#!/usr/bin/env python3
"""
Bootstrap script - Initial plugin/instance discovery
Populates database with current state before agent takesover monitoring
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_access import ConfigDatabase
from src.amp_integration.instance_scanner import AMPInstanceScanner
from src.agent.production_endpoint_agent import ProductionEndpointAgent

def main():
    """Run initial discovery"""
    print("=" * 60)
    print("Initial System Discovery - Bootstrap")
    print("=" * 60)
    print()
    
    # Database config
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    # Determine server name from hostname
    import socket
    hostname = socket.gethostname()
    # Auto-detect if possible, otherwise prompt
    if 'hetzner' in hostname.lower():
        server_name = 'hetzner-xeon'
    elif 'ovh' in hostname.lower():
        server_name = 'ovh-ryzen'
    else:
        server_name = input("Enter server name (hetzner-xeon or ovh-ryzen): ").strip()
    
    print(f"Server: {server_name}")
    print(f"Database: {db_config['database']}@{db_config['host']}:{db_config['port']}")
    print()
    
    # Create production agent (but don't start loop)
    agent = ProductionEndpointAgent(server_name, db_config)
    
    # Run one-time full discovery
    print("Running full discovery...")
    agent._run_full_discovery()
    
    print()
    print("=" * 60)
    print("Discovery Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Check database: SELECT COUNT(*) FROM plugins;")
    print("2. Start agent: sudo systemctl restart homeamp-agent")
    print(f"3. Check GUI: http://{db_config['host']}:8078/")


if __name__ == "__main__":
    main()
