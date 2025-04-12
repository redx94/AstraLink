"""
Cache Manager - Redis-based caching for monitoring system
"""
from typing import Dict, Any, Optional
import aioredis
import json
import time
from datetime import datetime, timedelta
import asyncio
from ..logging_config import get_logger
from ..config import config_manager

logger = get_logger(__name__)

class CacheManager:
    def __init__(self):
        self.config = config_manager.get_value('monitoring.cache', {})
        self.redis = None
        self._initialize_cache_config()
        asyncio.create_task(self._init_redis())
        asyncio.create_task(self._cache_maintenance_loop())

    def _initialize_cache_config(self):
        """Initialize cache configuration"""
        self.default_ttl = self.config.get('default_ttl', 300)  # 5 minutes
        self.max_cache_size = self.config.get('max_size', 10000)
        self.cache_prefix = self.config.get('prefix', 'astralink:monitoring:')
        self.compression_threshold = self.config.get('compression_threshold', 1024)  # 1KB
        
        # TTL configuration for different metric types
        self.ttl_config = {
            'high_frequency': 60,    # 1 minute for high-frequency metrics
            'medium_frequency': 300,  # 5 minutes for medium-frequency metrics
            'low_frequency': 3600,   # 1 hour for low-frequency metrics
            'archival': 86400        # 24 hours for archival data
        }

    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_config = self.config.get('redis', {})
            self.redis = await aioredis.create_redis_pool(
                f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}",
                password=redis_config.get('password'),
                minsize=5,
                maxsize=20,
                encoding='utf-8'
            )
            logger.info("Redis cache connection established")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            self.redis = None

    async def _cache_maintenance_loop(self):
        """Periodic cache maintenance"""
        while True:
            try:
                if self.redis:
                    # Clean up expired keys
                    await self._cleanup_expired_keys()
                    
                    # Check cache size and evict if needed
                    await self._check_cache_size()
                    
                    # Update cache statistics
                    await self._update_cache_stats()
                    
                await asyncio.sleep(300)  # Run maintenance every 5 minutes
                
            except Exception as e:
                logger.error(f"Cache maintenance failed: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_keys(self):
        """Clean up expired cache entries"""
        try:
            cursor = b'0'
            pattern = f"{self.cache_prefix}*"
            
            while cursor:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern
                )
                
                for key in keys:
                    # Check if key exists and get TTL
                    ttl = await self.redis.ttl(key)
                    if ttl < 0:  # Key exists but has no TTL or is expired
                        await self.redis.delete(key)
                        
            logger.debug("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    async def _check_cache_size(self):
        """Check and maintain cache size limits"""
        try:
            # Get cache info
            info = await self.redis.info('memory')
            used_memory = info['used_memory']
            
            if used_memory > self.max_cache_size:
                # Get all keys with their access time
                keys = []
                cursor = b'0'
                pattern = f"{self.cache_prefix}*"
                
                while cursor:
                    cursor, batch = await self.redis.scan(
                        cursor=cursor,
                        match=pattern
                    )
                    
                    for key in batch:
                        access_time = await self.redis.object('idletime', key)
                        keys.append((key, access_time))
                
                # Sort by access time (least recently used first)
                keys.sort(key=lambda x: x[1], reverse=True)
                
                # Remove oldest keys until under limit
                for key, _ in keys:
                    if used_memory <= self.max_cache_size:
                        break
                    
                    size = await self.redis.memory_usage(key)
                    await self.redis.delete(key)
                    used_memory -= size
                    
            logger.debug("Cache size check completed")
            
        except Exception as e:
            logger.error(f"Cache size check failed: {e}")

    async def _update_cache_stats(self):
        """Update cache statistics"""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'hits': 0,
                'misses': 0,
                'keys': 0,
                'memory_used': 0
            }
            
            if self.redis:
                info = await self.redis.info('stats')
                keyspace = await self.redis.info('keyspace')
                
                stats.update({
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'keys': sum(db.get('keys', 0) for db in keyspace.values()),
                    'memory_used': info.get('used_memory', 0)
                })
            
            # Store stats
            await self.set(
                'cache:stats',
                stats,
                ttl=3600  # Keep stats for 1 hour
            )
            
        except Exception as e:
            logger.error(f"Failed to update cache stats: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        try:
            if not self.redis:
                return default
                
            full_key = f"{self.cache_prefix}{key}"
            value = await self.redis.get(full_key)
            
            if value is None:
                return default
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if not self.redis:
                return False
                
            full_key = f"{self.cache_prefix}{key}"
            
            # Convert value to JSON if needed
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value)
                
            # Set with TTL
            expire = ttl or self.default_ttl
            await self.redis.set(full_key, value, expire=expire)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if not self.redis:
                return False
                
            full_key = f"{self.cache_prefix}{key}"
            await self.redis.delete(full_key)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False

    async def get_many(self, keys: list) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            if not self.redis:
                return {}
                
            # Prepare full keys
            full_keys = [f"{self.cache_prefix}{key}" for key in keys]
            
            # Get all values
            values = await self.redis.mget(*full_keys)
            
            # Process results
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
                        
            return result
            
        except Exception as e:
            logger.error(f"Cache get_many failed: {e}")
            return {}

    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        try:
            if not self.redis:
                return False
                
            pipe = self.redis.pipeline()
            expire = ttl or self.default_ttl
            
            for key, value in mapping.items():
                full_key = f"{self.cache_prefix}{key}"
                
                # Convert value to JSON if needed
                if not isinstance(value, (str, bytes)):
                    value = json.dumps(value)
                    
                pipe.set(full_key, value, expire=expire)
                
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Cache set_many failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = await self.get('cache:stats', {})
            if not stats:
                await self._update_cache_stats()
                stats = await self.get('cache:stats', {})
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

# Global cache manager instance
cache_manager = CacheManager()