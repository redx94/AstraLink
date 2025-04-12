"""
Rate Limiter - Implements token bucket and leaky bucket algorithms
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import aioredis
from ..logging_config import get_logger
from ..config import config_manager

logger = get_logger(__name__)

class RateLimitAlgorithm(Enum):
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

@dataclass
class RateLimitRule:
    key: str
    algorithm: RateLimitAlgorithm
    capacity: int
    refill_rate: float  # tokens per second
    window_size: Optional[int] = None  # seconds, for sliding window
    distributed: bool = False  # whether to use Redis for distributed rate limiting

class RateLimiter:
    """Rate limiter implementation"""
    def __init__(self):
        self.config = config_manager.get_value('rate_limiting', {})
        self.redis: Optional[aioredis.Redis] = None
        self._buckets: Dict[str, Dict[str, Any]] = {}
        self._initialize_buckets()
        
        # Start maintenance tasks
        asyncio.create_task(self._cleanup_buckets())
        asyncio.create_task(self._init_redis())

    def _initialize_buckets(self):
        """Initialize rate limit buckets from configuration"""
        try:
            # Load rules from config
            rules = self.config.get('rules', {})
            for key, rule in rules.items():
                self._buckets[key] = {
                    'tokens': rule.get('capacity', 100),
                    'capacity': rule.get('capacity', 100),
                    'refill_rate': rule.get('refill_rate', 1.0),
                    'last_refill': time.time(),
                    'algorithm': RateLimitAlgorithm(rule.get('algorithm', 'token_bucket')),
                    'window_size': rule.get('window_size'),
                    'requests': [],  # for leaky bucket
                    'distributed': rule.get('distributed', False)
                }
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limit buckets: {e}")

    async def _init_redis(self):
        """Initialize Redis connection for distributed rate limiting"""
        try:
            redis_config = self.config.get('redis', {})
            if redis_config:
                self.redis = await aioredis.create_redis_pool(
                    f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}",
                    password=redis_config.get('password'),
                    minsize=5,
                    maxsize=20
                )
                logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for rate limiting: {e}")

    async def _cleanup_buckets(self):
        """Periodic cleanup of rate limit buckets"""
        while True:
            try:
                current_time = time.time()
                
                # Clean up old requests from leaky buckets
                for bucket in self._buckets.values():
                    if bucket['algorithm'] == RateLimitAlgorithm.LEAKY_BUCKET:
                        window = bucket.get('window_size', 60)
                        bucket['requests'] = [
                            req for req in bucket['requests']
                            if current_time - req <= window
                        ]
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                logger.error(f"Rate limiter cleanup failed: {e}")
                await asyncio.sleep(5)

    async def _refill_tokens(self, bucket: Dict[str, Any]):
        """Refill tokens based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - bucket['last_refill']
        new_tokens = int(elapsed * bucket['refill_rate'])
        
        if new_tokens > 0:
            bucket['tokens'] = min(
                bucket['capacity'],
                bucket['tokens'] + new_tokens
            )
            bucket['last_refill'] = current_time

    async def _check_distributed_limit(self,
                                     key: str,
                                     bucket: Dict[str, Any],
                                     tokens: int = 1) -> bool:
        """Check rate limit using Redis for distributed scenarios"""
        try:
            if not self.redis:
                return True  # Fallback to local if Redis not available
            
            redis_key = f"ratelimit:{key}"
            current_time = int(time.time())
            
            # Use Redis for distributed token bucket
            if bucket['algorithm'] == RateLimitAlgorithm.TOKEN_BUCKET:
                pipe = self.redis.pipeline()
                # Get current tokens and last refill time
                pipe.hget(redis_key, "tokens")
                pipe.hget(redis_key, "last_refill")
                current_tokens, last_refill = await pipe.execute()
                
                current_tokens = int(current_tokens or bucket['capacity'])
                last_refill = float(last_refill or time.time())
                
                # Calculate token refill
                elapsed = current_time - last_refill
                new_tokens = int(elapsed * bucket['refill_rate'])
                current_tokens = min(bucket['capacity'], current_tokens + new_tokens)
                
                if current_tokens >= tokens:
                    # Update tokens atomically
                    pipe = self.redis.pipeline()
                    pipe.hset(redis_key, "tokens", current_tokens - tokens)
                    pipe.hset(redis_key, "last_refill", current_time)
                    await pipe.execute()
                    return True
                return False
                
            # Use Redis sorted set for distributed leaky bucket
            elif bucket['algorithm'] == RateLimitAlgorithm.LEAKY_BUCKET:
                window = bucket.get('window_size', 60)
                cutoff = current_time - window
                
                # Remove old requests
                await self.redis.zremrangebyscore(redis_key, 0, cutoff)
                
                # Count recent requests
                count = await self.redis.zcount(redis_key, cutoff, float('inf'))
                
                if count < bucket['capacity']:
                    # Add new request
                    await self.redis.zadd(redis_key, current_time, str(current_time))
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Distributed rate limit check failed: {e}")
            return True  # Fallback to allow on error

    async def check_limit(self, key: str, tokens: int = 1) -> bool:
        """Check if operation is allowed by rate limit"""
        try:
            if key not in self._buckets:
                return True  # No rate limit defined
                
            bucket = self._buckets[key]
            
            # Use distributed rate limiting if configured
            if bucket['distributed'] and self.redis:
                return await self._check_distributed_limit(key, bucket, tokens)
            
            # Token bucket algorithm
            if bucket['algorithm'] == RateLimitAlgorithm.TOKEN_BUCKET:
                await self._refill_tokens(bucket)
                if bucket['tokens'] >= tokens:
                    bucket['tokens'] -= tokens
                    return True
                return False
                
            # Leaky bucket algorithm
            elif bucket['algorithm'] == RateLimitAlgorithm.LEAKY_BUCKET:
                current_time = time.time()
                window = bucket.get('window_size', 60)
                
                # Remove old requests
                bucket['requests'] = [
                    req for req in bucket['requests']
                    if current_time - req <= window
                ]
                
                # Check if under capacity
                if len(bucket['requests']) < bucket['capacity']:
                    bucket['requests'].append(current_time)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {e}")
            return True  # Allow on error

    def create_rule(self, rule: RateLimitRule):
        """Create a new rate limit rule"""
        try:
            self._buckets[rule.key] = {
                'tokens': rule.capacity,
                'capacity': rule.capacity,
                'refill_rate': rule.refill_rate,
                'last_refill': time.time(),
                'algorithm': rule.algorithm,
                'window_size': rule.window_size,
                'requests': [],
                'distributed': rule.distributed
            }
            logger.info(f"Created rate limit rule for {rule.key}")
        except Exception as e:
            logger.error(f"Failed to create rate limit rule: {e}")

    def update_rule(self, key: str, updates: Dict[str, Any]):
        """Update an existing rate limit rule"""
        try:
            if key in self._buckets:
                bucket = self._buckets[key]
                for field, value in updates.items():
                    if field in bucket:
                        bucket[field] = value
                logger.info(f"Updated rate limit rule for {key}")
            else:
                logger.warning(f"Rate limit rule not found: {key}")
        except Exception as e:
            logger.error(f"Failed to update rate limit rule: {e}")

    def delete_rule(self, key: str):
        """Delete a rate limit rule"""
        try:
            if key in self._buckets:
                del self._buckets[key]
                logger.info(f"Deleted rate limit rule for {key}")
            else:
                logger.warning(f"Rate limit rule not found: {key}")
        except Exception as e:
            logger.error(f"Failed to delete rate limit rule: {e}")

    async def get_limit_status(self, key: str) -> Dict[str, Any]:
        """Get current status of a rate limit"""
        try:
            if key not in self._buckets:
                return {}
                
            bucket = self._buckets[key]
            current_time = time.time()
            
            if bucket['distributed'] and self.redis:
                redis_key = f"ratelimit:{key}"
                if bucket['algorithm'] == RateLimitAlgorithm.TOKEN_BUCKET:
                    tokens = await self.redis.hget(redis_key, "tokens")
                    last_refill = await self.redis.hget(redis_key, "last_refill")
                    return {
                        'tokens': int(tokens or bucket['capacity']),
                        'capacity': bucket['capacity'],
                        'last_refill': float(last_refill or current_time),
                        'algorithm': bucket['algorithm'].value
                    }
                else:  # Leaky bucket
                    count = await self.redis.zcount(
                        redis_key,
                        current_time - bucket.get('window_size', 60),
                        float('inf')
                    )
                    return {
                        'current_requests': count,
                        'capacity': bucket['capacity'],
                        'window_size': bucket.get('window_size', 60),
                        'algorithm': bucket['algorithm'].value
                    }
            else:
                if bucket['algorithm'] == RateLimitAlgorithm.TOKEN_BUCKET:
                    await self._refill_tokens(bucket)
                    return {
                        'tokens': bucket['tokens'],
                        'capacity': bucket['capacity'],
                        'last_refill': bucket['last_refill'],
                        'algorithm': bucket['algorithm'].value
                    }
                else:  # Leaky bucket
                    return {
                        'current_requests': len(bucket['requests']),
                        'capacity': bucket['capacity'],
                        'window_size': bucket.get('window_size', 60),
                        'algorithm': bucket['algorithm'].value
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get rate limit status for {key}: {e}")
            return {}

# Global rate limiter instance
rate_limiter = RateLimiter()