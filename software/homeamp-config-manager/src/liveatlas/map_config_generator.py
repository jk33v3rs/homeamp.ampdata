"""
LiveAtlas Multi-Server Configuration Generator

Automatically generates LiveAtlas index.html config for all Pl3xMap instances.
Separates public and private (BTS) maps with proper reverse proxy URLs.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Instance Classification
PUBLIC_INSTANCES = {
    "BENT01",
    "BIG01",
    "CLIP01",
    "CREA01",
    "DEV01",
    "EMAD01",
    "EVO01",
    "HARD01",
    "MINE01",
    "MIN01",
    "PRI01",
    "SMP101",
    "SMP201",
    "TOW01",
}

BTS_INSTANCES = {  # Behind-The-Scenes / Private maps (auth required)
    "ROY01",  # Battle Royale - hide player positions
    "CSMC01",  # Counter-Strike MC - anti-screen camping
}


class LiveAtlasConfigGenerator:
    """
    Generate LiveAtlas configuration for multi-server Pl3xMap setup.

    Key concepts:
    - Each Pl3xMap instance has internal web server on port 8080-8095
    - Reverse proxy routes: /map/{server_name}/ -> http://{internal_ip}:{port}/
    - LiveAtlas needs server dropdown config with all backend URLs
    - Two deployments: public map (open) and BTS map (auth required)
    """

    def __init__(self, db_connection):
        self.db = db_connection

        # Reverse proxy base URLs
        self.public_base_url = "https://map.archivesmp.site"
        self.bts_base_url = "https://btsmap.archivesmp.site"  # Behind auth

    def get_pl3xmap_instances(self) -> List[Dict]:
        """
        Query database for all instances with Pl3xMap installed.
        Reads actual port from each instance's Pl3xMap config.yml file.

        Returns:
            List of instance dicts with server, instance_id, folder_name, internal port
        """
        query = """
            SELECT 
                i.instance_id,
                i.instance_name,
                i.folder_name,
                i.server_name,
                i.internal_ip,
                ip.version as pl3xmap_version
            FROM instances i
            JOIN instance_plugins ip ON i.instance_id = ip.instance_id
            WHERE ip.plugin_id = 'pl3xmap'
                AND ip.is_installed = TRUE
                AND i.is_active = TRUE
            ORDER BY i.server_name, i.folder_name
        """

        results = self.db.execute_query(query, fetch=True)
        instances = []

        for row in results:
            instance = dict(row)

            # Read actual port from Pl3xMap config.yml
            config_path = self.get_pl3xmap_config_path(instance["server_name"], instance["folder_name"])
            instance["internal_port"] = self.get_internal_webserver_port(config_path)

            instances.append(instance)

        return instances

    def get_pl3xmap_config_path(self, server_name: str, folder_name: str) -> Path:
        """
        Get path to Pl3xMap config.yml for an instance.

        Args:
            server_name: hetzner-xeon or ovh-ryzen
            folder_name: Instance folder name (e.g., BENT01)

        Returns:
            Path to config.yml
        """
        if server_name == "hetzner-xeon":
            base = Path("/home/amp/.ampdata/instances")
        elif server_name == "ovh-ryzen":
            base = Path("/home/amp/.ampdata/instances")
        else:
            raise ValueError(f"Unknown server: {server_name}")

        return base / folder_name / "plugins" / "Pl3xMap" / "config.yml"

    def get_internal_webserver_port(self, config_path: Path) -> int:
        """
        Read Pl3xMap config.yml to get internal web server port.

        Args:
            config_path: Path to Pl3xMap config.yml

        Returns:
            Port number (default 8080 if not found or file doesn't exist)
        """
        if not config_path.exists():
            logger.warning(f"Pl3xMap config not found: {config_path}, using default port 8080")
            return 8080

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Pl3xMap config structure:
            # settings:
            #   internal-webserver:
            #     enabled: true
            #     bind: 0.0.0.0
            #     port: 8080

            if config and "settings" in config:
                webserver = config["settings"].get("internal-webserver", {})
                port = webserver.get("port", 8080)

                if webserver.get("enabled", True):
                    logger.debug(f"Read Pl3xMap port from config: {port}")
                    return port
                else:
                    logger.warning(f"Pl3xMap internal webserver disabled in {config_path}")
                    return 8080

            logger.warning(f"No settings.internal-webserver in {config_path}, using default")
            return 8080

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse Pl3xMap config {config_path}: {e}")
            return 8080
        except Exception as e:
            logger.error(f"Error reading Pl3xMap config {config_path}: {e}")
            return 8080

    def is_bts_instance(self, folder_name: str) -> bool:
        """Check if instance should be on BTS (private) map"""
        return folder_name.upper() in BTS_INSTANCES

    def generate_server_config(self, instance: Dict) -> Dict:
        """
        Generate LiveAtlas server config for one Pl3xMap instance.

        Per LiveAtlas wiki:
        - Pl3xmap servers only need the base URL
        - URL should point to Pl3xMap internal webserver (via reverse proxy)

        Example:
        {
            'bent01': {
                'label': 'BENT01 - Standard Survival',
                'pl3xmap': 'https://map.archivesmp.site/bent01/'
            }
        }

        Args:
            instance: Instance dict from database

        Returns:
            Server config dict
        """
        folder_name = instance["folder_name"]
        instance_name = instance["instance_name"] or folder_name

        # Determine which map domain to use
        is_bts = self.is_bts_instance(folder_name)
        base_url = self.bts_base_url if is_bts else self.public_base_url

        # Server key (used in URL: /map/{server_key})
        server_key = folder_name.lower()

        # Human-readable label
        label = f"{folder_name} - {instance_name}"
        if is_bts:
            label += " "  # Indicate private/restricted

        # Pl3xMap URL (reverse proxy will route to internal server)
        pl3xmap_url = f"{base_url}/{server_key}/"

        return {"key": server_key, "config": {"label": label, "pl3xmap": pl3xmap_url}}

    def generate_liveatlas_config(self, deployment: str = "public") -> Dict:
        """
        Generate complete LiveAtlas window.liveAtlasConfig object.

        Args:
            deployment: 'public' or 'bts' - determines which instances to include

        Returns:
            Config dict to inject into index.html
        """
        instances = self.get_pl3xmap_instances()

        servers = {}

        for instance in instances:
            folder_name = instance["folder_name"]
            is_bts = self.is_bts_instance(folder_name)

            # Filter by deployment type
            if deployment == "public" and is_bts:
                continue
            if deployment == "bts" and not is_bts:
                continue

            server_config = self.generate_server_config(instance)
            servers[server_config["key"]] = server_config["config"]

        config = {"servers": servers}

        logger.info(f"Generated LiveAtlas config for {deployment}: {len(servers)} servers")

        return config

    def generate_nginx_reverse_proxy_config(self, deployment: str = "public") -> str:
        """
        Generate nginx reverse proxy configuration for Pl3xMap servers.

        This routes subpaths to local Pl3xMap web servers:
        - https://map.archivesmp.site/bent01/ -> http://localhost:8080/
        - https://map.archivesmp.site/csmc01/ -> http://localhost:8081/

        Args:
            deployment: 'public' or 'bts'

        Returns:
            nginx config snippet
        """
        instances = self.get_pl3xmap_instances()

        base_domain = "map.archivesmp.site" if deployment == "public" else "btsmap.archivesmp.site"

        nginx_config = f"""
# LiveAtlas Multi-Server Reverse Proxy Config
# Generated: {datetime.now().isoformat()}
# Deployment: {deployment}

# Serve LiveAtlas static files
location /map/ {{
    root /var/www/{base_domain};
    index index.html;
    try_files $uri /map/index.html;
}}

# Reverse proxy to each Pl3xMap instance's internal webserver
"""

        for instance in instances:
            folder_name = instance["folder_name"]
            is_bts = self.is_bts_instance(folder_name)

            # Filter by deployment
            if deployment == "public" and is_bts:
                continue
            if deployment == "bts" and not is_bts:
                continue

            server_key = folder_name.lower()
            internal_ip = instance["internal_ip"]
            internal_port = instance["internal_port"]

            nginx_config += f"""
# {folder_name} - {instance['instance_name']}
location /map/{server_key}/ {{
    proxy_pass http://{internal_ip}:{internal_port}/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Pl3xMap SSE (Server-Sent Events) support
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
}}
"""

        return nginx_config

    def save_liveatlas_config(self, deployment: str, output_file: Path):
        """
        Save LiveAtlas config JSON to file.

        This should be injected into index.html <script> tag:
        <script>
            window.liveAtlasConfig = {{ ... }};
        </script>
        """
        config = self.generate_liveatlas_config(deployment)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved LiveAtlas config to {output_file}")

        return config

    def save_nginx_config(self, deployment: str, output_file: Path):
        """Save nginx reverse proxy config snippet"""
        config = self.generate_nginx_reverse_proxy_config(deployment)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(config)

        logger.info(f"Saved nginx config to {output_file}")

        return config


def main():
    """Generate configs for both public and BTS deployments"""
    from ..database.db_access import ConfigDatabase

    db = ConfigDatabase()
    db.connect()

    try:
        generator = LiveAtlasConfigGenerator(db)

        # Generate public map config
        public_config = generator.save_liveatlas_config("public", Path("/tmp/liveatlas-public-config.json"))
        public_nginx = generator.save_nginx_config("public", Path("/tmp/nginx-public-pl3xmap.conf"))

        # Generate BTS map config
        bts_config = generator.save_liveatlas_config("bts", Path("/tmp/liveatlas-bts-config.json"))
        bts_nginx = generator.save_nginx_config("bts", Path("/tmp/nginx-bts-pl3xmap.conf"))

        print("[OK] Generated LiveAtlas configs:")
        print(f"   Public: {len(public_config['servers'])} servers")
        print(f"   BTS: {len(bts_config['servers'])} servers")

    finally:
        db.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
