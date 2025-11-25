"""
LuckPerms Rank Parser

Parses LuckPerms group configuration files to discover and catalog rank hierarchies.
Supports both YAML and JSON configuration formats.
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RankInfo:
    """Represents a discovered LuckPerms rank/group"""

    instance_id: Optional[str] = None
    server_name: Optional[str] = None
    rank_name: str = ""
    priority: int = 0
    display_name: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    color_code: Optional[str] = None
    permission_count: int = 0
    inherits_from: List[str] = None
    discovered_at: datetime = None
    is_active: bool = True
    is_default: bool = False
    player_count: int = 0

    def __post_init__(self):
        if self.inherits_from is None:
            self.inherits_from = []
        if self.discovered_at is None:
            self.discovered_at = datetime.now()


class LuckPermsRankParser:
    """Parse LuckPerms group configuration files"""

    def __init__(self):
        self.ranks: List[RankInfo] = []

    def parse_group_file(
        self, file_path: Path, instance_id: Optional[str] = None, server_name: Optional[str] = None
    ) -> RankInfo:
        """
        Parse a single LuckPerms group file.

        Args:
            file_path: Path to group YAML/JSON file
            instance_id: Instance identifier (optional)
            server_name: Server name (optional)

        Returns:
            RankInfo object
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Group file not found: {file_path}")

        # Determine format from extension
        if file_path.suffix in [".yml", ".yaml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return self._parse_group_data(data, file_path.stem, instance_id, server_name)

    def _parse_group_data(
        self, data: Dict[str, Any], rank_name: str, instance_id: Optional[str] = None, server_name: Optional[str] = None
    ) -> RankInfo:
        """
        Parse LuckPerms group data from dict.

        Args:
            data: Parsed YAML/JSON data
            rank_name: Group name (from filename)
            instance_id: Instance identifier
            server_name: Server name

        Returns:
            RankInfo object
        """
        # Extract basic info
        display_name = data.get("displayname") or data.get("display-name") or rank_name
        priority = data.get("weight", 0)  # LuckPerms uses 'weight'

        # Extract inheritance
        inherits_from = []
        parents = data.get("parents", [])
        if isinstance(parents, list):
            inherits_from = parents
        elif isinstance(parents, dict):
            # Some configs use dict format with contexts
            inherits_from = list(parents.keys())

        # Count permissions
        permissions = data.get("permissions", {})
        permission_count = len(permissions) if isinstance(permissions, dict) else 0

        # Extract chat formatting (prefix/suffix)
        prefix, suffix, color_code = self._extract_chat_formatting(data)

        # Check if default group
        is_default = data.get("default", False) or rank_name.lower() == "default"

        return RankInfo(
            instance_id=instance_id,
            server_name=server_name,
            rank_name=rank_name,
            priority=priority,
            display_name=display_name,
            prefix=prefix,
            suffix=suffix,
            color_code=color_code,
            permission_count=permission_count,
            inherits_from=inherits_from,
            is_default=is_default,
            is_active=True,
        )

    def _extract_chat_formatting(self, data: Dict[str, Any]) -> tuple:
        """
        Extract prefix, suffix, and color code from group data.

        Args:
            data: Group configuration dict

        Returns:
            Tuple of (prefix, suffix, color_code)
        """
        prefix = None
        suffix = None
        color_code = None

        # Check for meta section (common in LuckPerms configs)
        meta = data.get("meta", {})

        # Try to find prefix
        if "prefix" in meta:
            prefix = meta["prefix"]
        elif "prefix" in data:
            prefix = data["prefix"]

        # Extract color code from prefix if present
        if prefix:
            color_code = self._extract_color_code(prefix)

        # Try to find suffix
        if "suffix" in meta:
            suffix = meta["suffix"]
        elif "suffix" in data:
            suffix = data["suffix"]

        return prefix, suffix, color_code

    def _extract_color_code(self, text: str) -> Optional[str]:
        """
        Extract Minecraft color code from formatted text.

        Args:
            text: Text containing color codes (e.g., "&c[Admin]")

        Returns:
            Color code (e.g., "&c") or None
        """
        import re

        # Match & color codes (&0-9, &a-f)
        match = re.search(r"&[0-9a-fk-or]", text)
        if match:
            return match.group(0)

        # Match § color codes (§0-9, §a-f)
        match = re.search(r"§[0-9a-fk-or]", text)
        if match:
            return match.group(0)

        return None

    def scan_luckperms_directory(
        self, luckperms_path: Path, instance_id: Optional[str] = None, server_name: Optional[str] = None
    ) -> List[RankInfo]:
        """
        Scan a LuckPerms directory for all group files.

        Args:
            luckperms_path: Path to LuckPerms plugin directory
            instance_id: Instance identifier
            server_name: Server name

        Returns:
            List of RankInfo objects
        """
        ranks = []

        # LuckPerms stores groups in different locations depending on storage type
        possible_group_paths = [
            luckperms_path / "groups",  # Flatfile storage
            luckperms_path / "yaml-storage" / "groups",  # YAML storage
            luckperms_path / "json-storage" / "groups",  # JSON storage
        ]

        for group_path in possible_group_paths:
            if not group_path.exists():
                continue

            logger.info(f"Scanning for groups in: {group_path}")

            # Scan for YAML files
            for group_file in group_path.glob("*.yml"):
                try:
                    rank = self.parse_group_file(group_file, instance_id, server_name)
                    ranks.append(rank)
                    logger.debug(f"Parsed rank: {rank.rank_name}")
                except Exception as e:
                    logger.error(f"Failed to parse {group_file.name}: {e}")

            # Scan for YAML files (alternate extension)
            for group_file in group_path.glob("*.yaml"):
                try:
                    rank = self.parse_group_file(group_file, instance_id, server_name)
                    ranks.append(rank)
                    logger.debug(f"Parsed rank: {rank.rank_name}")
                except Exception as e:
                    logger.error(f"Failed to parse {group_file.name}: {e}")

            # Scan for JSON files
            for group_file in group_path.glob("*.json"):
                try:
                    rank = self.parse_group_file(group_file, instance_id, server_name)
                    ranks.append(rank)
                    logger.debug(f"Parsed rank: {rank.rank_name}")
                except Exception as e:
                    logger.error(f"Failed to parse {group_file.name}: {e}")

        if ranks:
            logger.info(f"Found {len(ranks)} ranks in {luckperms_path}")

        return ranks

    def scan_instance(self, instance_path: Path, instance_id: str, server_name: Optional[str] = None) -> List[RankInfo]:
        """
        Scan an instance directory for LuckPerms ranks.

        Args:
            instance_path: Path to instance directory
            instance_id: Instance identifier
            server_name: Server name (optional)

        Returns:
            List of RankInfo objects
        """
        # Look for LuckPerms plugin directory
        luckperms_paths = [
            instance_path / "plugins" / "LuckPerms",
            instance_path / "plugins" / "luckperms",
            instance_path / "mods" / "luckperms",  # Fabric/Forge
        ]

        for luckperms_path in luckperms_paths:
            if luckperms_path.exists():
                return self.scan_luckperms_directory(luckperms_path, instance_id, server_name)

        logger.warning(f"LuckPerms not found in instance: {instance_id}")
        return []

    def scan_all_instances(
        self, instance_registry: Dict[str, Path], server_name: Optional[str] = None
    ) -> Dict[str, List[RankInfo]]:
        """
        Scan all instances for LuckPerms ranks.

        Args:
            instance_registry: Dict mapping instance_id to instance_path
            server_name: Server name for all instances (optional)

        Returns:
            Dict mapping instance_id to list of RankInfo objects
        """
        all_ranks = {}

        for instance_id, instance_path in instance_registry.items():
            logger.info(f"Scanning instance for ranks: {instance_id}")
            ranks = self.scan_instance(instance_path, instance_id, server_name)
            all_ranks[instance_id] = ranks
            logger.info(f"Found {len(ranks)} ranks in {instance_id}")

        return all_ranks


class RankDatabaseImporter:
    """Import discovered ranks into database"""

    def __init__(self, db_connection):
        """
        Initialize with database connection.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def insert_rank(self, rank: RankInfo) -> int:
        """
        Insert a rank into the database.

        Args:
            rank: RankInfo object

        Returns:
            Inserted rank_id
        """
        import json

        cursor = self.db.cursor()

        query = """
        INSERT INTO ranks (
            instance_id, server_name, rank_name, priority,
            display_name, prefix, suffix, color_code,
            permission_count, inherits_from,
            discovered_at, last_seen_at, is_active, is_default, player_count
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            priority = VALUES(priority),
            display_name = VALUES(display_name),
            prefix = VALUES(prefix),
            suffix = VALUES(suffix),
            color_code = VALUES(color_code),
            permission_count = VALUES(permission_count),
            inherits_from = VALUES(inherits_from),
            last_seen_at = VALUES(last_seen_at),
            is_active = VALUES(is_active),
            is_default = VALUES(is_default)
        """

        cursor.execute(
            query,
            (
                rank.instance_id,
                rank.server_name,
                rank.rank_name,
                rank.priority,
                rank.display_name,
                rank.prefix,
                rank.suffix,
                rank.color_code,
                rank.permission_count,
                json.dumps(rank.inherits_from),
                rank.discovered_at,
                datetime.now(),  # last_seen_at
                rank.is_active,
                rank.is_default,
                rank.player_count,
            ),
        )

        self.db.commit()
        return cursor.lastrowid

    def bulk_insert_ranks(self, ranks: List[RankInfo]) -> int:
        """
        Bulk insert multiple ranks.

        Args:
            ranks: List of RankInfo objects

        Returns:
            Number of rows affected
        """
        import json

        if not ranks:
            return 0

        cursor = self.db.cursor()

        query = """
        INSERT INTO ranks (
            instance_id, server_name, rank_name, priority,
            display_name, prefix, suffix, color_code,
            permission_count, inherits_from,
            discovered_at, last_seen_at, is_active, is_default, player_count
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            priority = VALUES(priority),
            display_name = VALUES(display_name),
            prefix = VALUES(prefix),
            suffix = VALUES(suffix),
            color_code = VALUES(color_code),
            permission_count = VALUES(permission_count),
            inherits_from = VALUES(inherits_from),
            last_seen_at = VALUES(last_seen_at),
            is_active = VALUES(is_active),
            is_default = VALUES(is_default)
        """

        values = [
            (
                rank.instance_id,
                rank.server_name,
                rank.rank_name,
                rank.priority,
                rank.display_name,
                rank.prefix,
                rank.suffix,
                rank.color_code,
                rank.permission_count,
                json.dumps(rank.inherits_from),
                rank.discovered_at,
                datetime.now(),  # last_seen_at
                rank.is_active,
                rank.is_default,
                rank.player_count,
            )
            for rank in ranks
        ]

        cursor.executemany(query, values)
        self.db.commit()

        return cursor.rowcount

    def import_scan_results(self, scan_results: Dict[str, List[RankInfo]]) -> Dict[str, int]:
        """
        Import all scan results into database.

        Args:
            scan_results: Dict mapping instance_id to list of RankInfo

        Returns:
            Dict mapping instance_id to number of ranks imported
        """
        results = {}

        for instance_id, ranks in scan_results.items():
            count = self.bulk_insert_ranks(ranks)
            results[instance_id] = count
            logger.info(f"Imported {count} ranks for instance {instance_id}")

        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: Parse a single group file
    parser = LuckPermsRankParser()

    group_file = Path("/path/to/plugins/LuckPerms/groups/admin.yml")
    if group_file.exists():
        rank = parser.parse_group_file(group_file, instance_id="BENT01", server_name="hetzner")
        print(f"\nParsed rank: {rank.rank_name}")
        print(f"  Display: {rank.display_name}")
        print(f"  Priority: {rank.priority}")
        print(f"  Prefix: {rank.prefix}")
        print(f"  Inherits: {', '.join(rank.inherits_from)}")
        print(f"  Permissions: {rank.permission_count}")

    # Example: Scan instance
    ranks = parser.scan_instance(
        instance_path=Path("/path/to/Servers/BENT01"), instance_id="BENT01", server_name="hetzner"
    )

    print(f"\nDiscovered {len(ranks)} ranks:")
    for rank in sorted(ranks, key=lambda r: r.priority, reverse=True):
        print(f"  [{rank.priority:4d}] {rank.rank_name} - {rank.display_name}")

    # Example: Import to database
    # import mysql.connector
    # db = mysql.connector.connect(...)
    # importer = RankDatabaseImporter(db)
    # count = importer.bulk_insert_ranks(ranks)
    # print(f"Imported {count} ranks to database")
