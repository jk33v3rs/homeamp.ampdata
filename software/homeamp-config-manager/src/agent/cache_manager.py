"""
Redis Cache Manager for ArchiveSMP Config Manager

Provides caching for frequently accessed data
"""

import json
from typing import Any, Optional
import logging
from datetime import timedelta

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger("cache_manager")


class CacheManager:
    """Manages Redis cache operations"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize cache manager
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional password
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        
        if not enabled:
            logger.info("Cache manager initialized but disabled")
            self.redis = None
            return
        
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache MISS: {key}")
            return None
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 5 minutes)
        
        Returns:
            Success status
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            Success status
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "instances:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            
            if keys:
                count = self.redis.delete(*keys)
                logger.info(f"Cache invalidated {count} keys matching '{pattern}'")
                return count
            
            return 0
        
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Cache stats
        """
        if not self.enabled or not self.redis:
            return {'enabled': False}
        
        try:
            info = self.redis.info('stats')
            return {
                'enabled': True,
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info),
                'keys': self.redis.dbsize()
            }
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    # ========================================================================
    # CONVENIENCE METHODS FOR COMMON CACHE KEYS
    # ========================================================================
    
    def get_instance(self, instance_id: str) -> Optional[dict]:
        """Get cached instance data"""
        return self.get(f"instance:{instance_id}")
    
    def set_instance(self, instance_id: str, data: dict, ttl: int = 300):
        """Cache instance data"""
        return self.set(f"instance:{instance_id}", data, ttl)
    
    def get_plugin_config(self, instance_id: str, plugin_name: str) -> Optional[dict]:
        """Get cached plugin config"""
        return self.get(f"config:{instance_id}:{plugin_name}")
    
    def set_plugin_config(
        self,
        instance_id: str,
        plugin_name: str,
        config: dict,
        ttl: int = 600
    ):
        """Cache plugin config"""
        return self.set(f"config:{instance_id}:{plugin_name}", config, ttl)
    
    def get_variance_report(self) -> Optional[dict]:
        """Get cached variance report"""
        return self.get("variance:report")
    
    def set_variance_report(self, report: dict, ttl: int = 1800):
        """Cache variance report (30 min TTL)"""
        return self.set("variance:report", report, ttl)
    
    def invalidate_instance(self, instance_id: str):
        """Invalidate all cache for an instance"""
        return self.invalidate_pattern(f"*:{instance_id}:*")
    
    def invalidate_plugin(self, plugin_name: str):
        """Invalidate all cache for a plugin"""
        return self.invalidate_pattern(f"*:{plugin_name}")
    
    def flush_all(self) -> bool:
        """
        Flush entire cache (use with caution)
        
        Returns:
            Success status
        """
        if not self.enabled or not self.redis:
            return False
        
        try:
            self.redis.flushdb()
            logger.warning("Cache flushed - all keys deleted")
            return True
        
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


def create_cache_manager(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    enabled: bool = True
) -> CacheManager:
    """
    Factory function to create cache manager
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Optional password
        enabled: Whether to enable caching
    
    Returns:
        CacheManager instance
    """
    return CacheManager(host, port, db, password, enabled)
