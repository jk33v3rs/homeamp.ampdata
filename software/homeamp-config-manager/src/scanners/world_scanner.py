"""
World Discovery Scanner

Scans Minecraft instance directories to discover and catalog all worlds.
Extracts world metadata including type, seed, generator, and size metrics.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import struct

logger = logging.getLogger(__name__)


@dataclass
class WorldInfo:
    """Represents discovered world information"""

    instance_id: str
    world_name: str
    world_type: str  # normal, nether, end, custom
    seed: Optional[int] = None
    generator: Optional[str] = None
    environment: Optional[str] = None
    folder_size_bytes: int = 0
    region_count: int = 0
    last_modified: Optional[datetime] = None
    discovered_at: datetime = None
    is_active: bool = True

    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()


class WorldScanner:
    """Scan instance directories for Minecraft worlds"""

    # Common world folder patterns
    WORLD_PATTERNS = [
        "world",
        "world_nether",
        "world_the_end",
        "*_world",
        "creative*",
        "survival*",
        "skyblock*",
        "plots*",
        "minigames*",
    ]

    # Dimension folder names
    DIMENSION_FOLDERS = {"DIM-1": "nether", "DIM1": "end", "region": "normal"}

    def __init__(self, instances_base_path: Path):
        """
        Initialize world scanner.

        Args:
            instances_base_path: Base path where instance directories are located
                                (e.g., /path/to/Servers/)
        """
        self.base_path = instances_base_path

    def scan_instance(self, instance_id: str, instance_path: Path) -> List[WorldInfo]:
        """
        Scan a single instance for worlds.

        Args:
            instance_id: Instance identifier
            instance_path: Path to instance directory

        Returns:
            List of discovered WorldInfo objects
        """
        worlds = []

        if not instance_path.exists():
            logger.warning(f"Instance path does not exist: {instance_path}")
            return worlds

        # Look for level.dat files (indicates world root)
        for level_dat in instance_path.rglob("level.dat"):
            world_path = level_dat.parent

            # Skip if inside dimension folders (DIM-1, DIM1)
            if any(dim in world_path.parts for dim in ["DIM-1", "DIM1", "DIM0"]):
                continue

            world_name = world_path.name
            logger.debug(f"Found world: {world_name} in {instance_id}")

            try:
                world_info = self._extract_world_info(
                    instance_id=instance_id, world_name=world_name, world_path=world_path
                )
                worlds.append(world_info)
            except Exception as e:
                logger.error(f"Error extracting world info for {world_name}: {e}")

        return worlds

    def _extract_world_info(self, instance_id: str, world_name: str, world_path: Path) -> WorldInfo:
        """
        Extract detailed information about a world.

        Args:
            instance_id: Instance identifier
            world_name: World folder name
            world_path: Path to world directory

        Returns:
            WorldInfo object
        """
        # Read level.dat
        level_dat_path = world_path / "level.dat"
        level_data = self._read_level_dat(level_dat_path)

        # Determine world type
        world_type = self._determine_world_type(world_name, world_path, level_data)

        # Get world properties
        seed = level_data.get("Data", {}).get("WorldGenSettings", {}).get("seed")
        generator = level_data.get("Data", {}).get("generatorName")

        # Calculate folder size and region count
        folder_size = self._calculate_folder_size(world_path)
        region_count = self._count_region_files(world_path)

        # Get last modification time
        last_modified = datetime.fromtimestamp(level_dat_path.stat().st_mtime)

        return WorldInfo(
            instance_id=instance_id,
            world_name=world_name,
            world_type=world_type,
            seed=seed,
            generator=generator,
            environment=world_type,  # Can be refined from level.dat
            folder_size_bytes=folder_size,
            region_count=region_count,
            last_modified=last_modified,
            is_active=True,
        )

    def _read_level_dat(self, level_dat_path: Path) -> Dict[str, Any]:
        """
        Read and parse level.dat NBT file.

        Note: This is a simplified parser. For production, use nbtlib or similar.

        Args:
            level_dat_path: Path to level.dat file

        Returns:
            Dictionary of level data (simplified)
        """
        try:
            # Try reading with nbtlib if available
            try:
                import nbtlib

                nbt_file = nbtlib.load(level_dat_path)
                return nbt_file.unpack()
            except ImportError:
                logger.debug("nbtlib not available, using simplified parser")
        except Exception as e:
            logger.warning(f"Failed to parse level.dat with nbtlib: {e}")

        # Fallback: Return empty dict (can't parse without NBT library)
        logger.warning(f"Cannot parse {level_dat_path} - nbtlib not installed")
        return {}

    def _determine_world_type(self, world_name: str, world_path: Path, level_data: Dict[str, Any]) -> str:
        """
        Determine world type from name, folder structure, or level data.

        Args:
            world_name: World folder name
            world_path: Path to world directory
            level_data: Parsed level.dat data

        Returns:
            World type: 'normal', 'nether', 'end', or 'custom'
        """
        # Check folder name patterns
        world_name_lower = world_name.lower()

        if "nether" in world_name_lower or "dim-1" in world_name_lower:
            return "nether"
        elif ("end" in world_name_lower or "dim1" in world_name_lower) and "the" in world_name_lower:
            return "end"

        # Check for dimension folders (indicates multiworld setup)
        has_nether = (world_path / "DIM-1").exists()
        has_end = (world_path / "DIM1").exists()
        has_region = (world_path / "region").exists()

        if has_region and (has_nether or has_end):
            return "normal"  # Main overworld with dimensions

        # Check level.dat for generator type
        generator = level_data.get("Data", {}).get("generatorName", "").lower()
        if generator and generator != "default":
            return "custom"

        # Default to normal
        return "normal"

    def _calculate_folder_size(self, world_path: Path) -> int:
        """
        Calculate total size of world folder in bytes.

        Args:
            world_path: Path to world directory

        Returns:
            Total size in bytes
        """
        total_size = 0

        try:
            for entry in world_path.rglob("*"):
                if entry.is_file():
                    total_size += entry.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating folder size for {world_path}: {e}")

        return total_size

    def _count_region_files(self, world_path: Path) -> int:
        """
        Count region files (.mca) in world.

        Args:
            world_path: Path to world directory

        Returns:
            Number of region files
        """
        region_count = 0

        # Count in overworld region folder
        region_path = world_path / "region"
        if region_path.exists():
            region_count += sum(1 for f in region_path.glob("*.mca"))

        # Count in nether region folder
        nether_region = world_path / "DIM-1" / "region"
        if nether_region.exists():
            region_count += sum(1 for f in nether_region.glob("*.mca"))

        # Count in end region folder
        end_region = world_path / "DIM1" / "region"
        if end_region.exists():
            region_count += sum(1 for f in end_region.glob("*.mca"))

        return region_count

    def scan_all_instances(self, instance_registry: Dict[str, Path]) -> Dict[str, List[WorldInfo]]:
        """
        Scan all instances for worlds.

        Args:
            instance_registry: Dict mapping instance_id to instance_path

        Returns:
            Dict mapping instance_id to list of WorldInfo objects
        """
        all_worlds = {}

        for instance_id, instance_path in instance_registry.items():
            logger.info(f"Scanning instance: {instance_id}")
            worlds = self.scan_instance(instance_id, instance_path)
            all_worlds[instance_id] = worlds
            logger.info(f"Found {len(worlds)} worlds in {instance_id}")

        return all_worlds


class WorldDatabaseImporter:
    """Import discovered worlds into database"""

    def __init__(self, db_connection):
        """
        Initialize with database connection.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def insert_world(self, world: WorldInfo) -> int:
        """
        Insert a world into the database.

        Args:
            world: WorldInfo object

        Returns:
            Inserted world_id
        """
        cursor = self.db.cursor()

        query = """
        INSERT INTO worlds (
            instance_id, world_name, world_type,
            seed, generator, environment,
            folder_size_bytes, region_count, last_modified,
            discovered_at, last_seen_at, is_active
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            world_type = VALUES(world_type),
            seed = VALUES(seed),
            generator = VALUES(generator),
            environment = VALUES(environment),
            folder_size_bytes = VALUES(folder_size_bytes),
            region_count = VALUES(region_count),
            last_modified = VALUES(last_modified),
            last_seen_at = VALUES(last_seen_at),
            is_active = VALUES(is_active)
        """

        cursor.execute(
            query,
            (
                world.instance_id,
                world.world_name,
                world.world_type,
                world.seed,
                world.generator,
                world.environment,
                world.folder_size_bytes,
                world.region_count,
                world.last_modified,
                world.discovered_at,
                datetime.now(),  # last_seen_at
                world.is_active,
            ),
        )

        self.db.commit()
        return cursor.lastrowid

    def bulk_insert_worlds(self, worlds: List[WorldInfo]) -> int:
        """
        Bulk insert multiple worlds.

        Args:
            worlds: List of WorldInfo objects

        Returns:
            Number of rows affected
        """
        if not worlds:
            return 0

        cursor = self.db.cursor()

        query = """
        INSERT INTO worlds (
            instance_id, world_name, world_type,
            seed, generator, environment,
            folder_size_bytes, region_count, last_modified,
            discovered_at, last_seen_at, is_active
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            world_type = VALUES(world_type),
            seed = VALUES(seed),
            generator = VALUES(generator),
            environment = VALUES(environment),
            folder_size_bytes = VALUES(folder_size_bytes),
            region_count = VALUES(region_count),
            last_modified = VALUES(last_modified),
            last_seen_at = VALUES(last_seen_at),
            is_active = VALUES(is_active)
        """

        values = [
            (
                world.instance_id,
                world.world_name,
                world.world_type,
                world.seed,
                world.generator,
                world.environment,
                world.folder_size_bytes,
                world.region_count,
                world.last_modified,
                world.discovered_at,
                datetime.now(),  # last_seen_at
                world.is_active,
            )
            for world in worlds
        ]

        cursor.executemany(query, values)
        self.db.commit()

        return cursor.rowcount

    def import_scan_results(self, scan_results: Dict[str, List[WorldInfo]]) -> Dict[str, int]:
        """
        Import all scan results into database.

        Args:
            scan_results: Dict mapping instance_id to list of WorldInfo

        Returns:
            Dict mapping instance_id to number of worlds imported
        """
        results = {}

        for instance_id, worlds in scan_results.items():
            count = self.bulk_insert_worlds(worlds)
            results[instance_id] = count
            logger.info(f"Imported {count} worlds for instance {instance_id}")

        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: Scan a single instance
    scanner = WorldScanner(Path("/path/to/Servers"))

    worlds = scanner.scan_instance(instance_id="BENT01", instance_path=Path("/path/to/Servers/BENT01"))

    print(f"\nDiscovered {len(worlds)} worlds:")
    for world in worlds:
        print(f"  {world.world_name} ({world.world_type})")
        print(f"    Size: {world.folder_size_bytes / 1024 / 1024:.2f} MB")
        print(f"    Regions: {world.region_count}")
        print(f"    Seed: {world.seed}")

    # Example: Import to database
    # import mysql.connector
    # db = mysql.connector.connect(...)
    # importer = WorldDatabaseImporter(db)
    # count = importer.bulk_insert_worlds(worlds)
    # print(f"Imported {count} worlds to database")
