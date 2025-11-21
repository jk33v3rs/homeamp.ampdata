"""
Datapack Discovery - Scans world folders for datapacks
"""
import mysql.connector
import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Datapack:
    """Represents a discovered datapack"""
    name: str
    version: Optional[str]
    world_path: str
    instance_id: str
    pack_format: Optional[int]
    description: Optional[str]


class DatapackDiscovery:
    """Discovers and tracks datapacks across all instances"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or get_db_config()
        self.world_folders = ['world', 'world_nether', 'world_the_end']
    
    def _get_db_connection(self):
        """Create database connection"""
        return get_db_connection()
    
    def extract_pack_metadata(self, datapack_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from pack.mcmeta file"""
        mcmeta_path = os.path.join(datapack_path, 'pack.mcmeta')
        
        if not os.path.exists(mcmeta_path):
            logger.warning(f"pack.mcmeta not found in {datapack_path}")
            return None
        
        try:
            with open(mcmeta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                pack_info = metadata.get('pack', {})
                custom_info = metadata.get('custom', {})
                
                return {
                    'pack_format': pack_info.get('format'),
                    'description': pack_info.get('description', ''),
                    'version': custom_info.get('version')  # Custom field, may not exist
                }
        except Exception as e:
            logger.error(f"Error reading pack.mcmeta at {mcmeta_path}: {e}")
            return None
    
    def scan_world_datapacks(self, instance_path: str, instance_id: str) -> List[Datapack]:
        """Scan all world folders in an instance for datapacks"""
        datapacks = []
        
        for world_folder in self.world_folders:
            world_path = os.path.join(instance_path, world_folder)
            datapacks_path = os.path.join(world_path, 'datapacks')
            
            if not os.path.exists(datapacks_path):
                logger.debug(f"Datapacks folder not found: {datapacks_path}")
                continue
            
            try:
                # List all subdirectories in datapacks folder
                for item in os.listdir(datapacks_path):
                    datapack_full_path = os.path.join(datapacks_path, item)
                    
                    # Skip files, only process directories
                    if not os.path.isdir(datapack_full_path):
                        continue
                    
                    # Extract metadata
                    metadata = self.extract_pack_metadata(datapack_full_path)
                    
                    if metadata:
                        datapack = Datapack(
                            name=item,
                            version=metadata.get('version'),
                            world_path=f"{world_folder}/datapacks/{item}",
                            instance_id=instance_id,
                            pack_format=metadata.get('pack_format'),
                            description=metadata.get('description')
                        )
                        datapacks.append(datapack)
                        logger.info(f"Found datapack: {item} in {instance_id}/{world_folder}")
                    else:
                        logger.warning(f"Could not extract metadata for {item} in {instance_id}/{world_folder}")
            except Exception as e:
                logger.error(f"Error scanning datapacks in {datapacks_path}: {e}")
        
        return datapacks
    
    def register_datapack(self, datapack: Datapack) -> int:
        """Register a datapack in the database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if datapack already exists
            cursor.execute("""
                SELECT id FROM datapacks
                WHERE instance_id = %s AND name = %s AND world_path = %s
            """, (datapack.instance_id, datapack.name, datapack.world_path))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing datapack
                cursor.execute("""
                    UPDATE datapacks
                    SET version = %s, pack_format = %s, description = %s
                    WHERE id = %s
                """, (datapack.version, datapack.pack_format, datapack.description, existing[0]))
                datapack_id = existing[0]
                logger.info(f"Updated datapack ID {datapack_id}: {datapack.name}")
            else:
                # Insert new datapack
                cursor.execute("""
                    INSERT INTO datapacks
                    (name, version, world_path, instance_id, pack_format, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (datapack.name, datapack.version, datapack.world_path, 
                      datapack.instance_id, datapack.pack_format, datapack.description))
                datapack_id = cursor.lastrowid
                logger.info(f"Registered new datapack ID {datapack_id}: {datapack.name}")
            
            conn.commit()
            return datapack_id
        finally:
            cursor.close()
            conn.close()
    
    def scan_and_register_all(self, instances: List[Dict[str, str]]) -> int:
        """Scan all instances for datapacks and register them"""
        total_datapacks = 0
        
        for instance in instances:
            instance_id = instance['instance_id']
            instance_path = instance['instance_path']
            
            logger.info(f"Scanning datapacks for instance {instance_id}...")
            datapacks = self.scan_world_datapacks(instance_path, instance_id)
            
            for datapack in datapacks:
                self.register_datapack(datapack)
                total_datapacks += 1
        
        logger.info(f"Total datapacks registered: {total_datapacks}")
        return total_datapacks
