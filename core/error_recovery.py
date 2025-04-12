"""
Error Recovery Manager - Handles error recovery for database and cache operations
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List, TypeVar, Awaitable
from dataclasses import dataclass
import time
from enum import Enum
import functools
from ..logging_config import get_logger
from ..config import config_manager
from .connection_pool import pool_manager

logger = get_logger(__name__)

T = TypeVar('T')  # Generic type for operation results

class OperationType(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    TRANSACTION = "transaction"

class ResourceType(Enum):
    DATABASE = "database"
    CACHE = "cache"
    BLOCKCHAIN = "blockchain"
    QUANTUM = "quantum"

@dataclass
class RetryConfig:
    max_attempts: int
    initial_delay: float
    max_delay: float
    exponential_base: float
    jitter: float

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int
    reset_timeout: float
    half_open_requests: int

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"
        self.half_open_successes = 0

    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.config.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")

    def record_success(self):
        """Record a success and potentially close the circuit"""
        if self.state == "half-open":
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.half_open_requests:
                self.reset()
                logger.info("Circuit breaker closed after successful half-open state")
        else:
            self.reset()

    def reset(self):
        """Reset the circuit breaker"""
        self.failures = 0
        self.state = "closed"
        self.half_open_successes = 0

    def allow_request(self) -> bool:
        """Check if a request should be allowed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time >= self.config.reset_timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    def __init__(self):
        self.config = config_manager.get_value('error_recovery', {})
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self._initialize_configs()
        
        # Start monitoring task
        asyncio.create_task(self._monitor_circuit_breakers())

    def _initialize_configs(self):
        """Initialize retry and circuit breaker configurations"""
        # Initialize retry configs
        for resource_type in ResourceType:
            self.retry_configs[resource_type.value] = RetryConfig(
                max_attempts=self.config.get('retry', {}).get('max_attempts', 3),
                initial_delay=self.config.get('retry', {}).get('initial_delay', 0.1),
                max_delay=self.config.get('retry', {}).get('max_delay', 2.0),
                exponential_base=self.config.get('retry', {}).get('exponential_base', 2.0),
                jitter=self.config.get('retry', {}).get('jitter', 0.1)
            )
        
        # Initialize circuit breakers
        for resource_type in ResourceType:
            self.circuit_breakers[resource_type.value] = CircuitBreaker(
                CircuitBreakerConfig(
                    failure_threshold=self.config.get('circuit_breaker', {}).get('failure_threshold', 5),
                    reset_timeout=self.config.get('circuit_breaker', {}).get('reset_timeout', 60),
                    half_open_requests=self.config.get('circuit_breaker', {}).get('half_open_requests', 3)
                )
            )

    async def _monitor_circuit_breakers(self):
        """Monitor and log circuit breaker states"""
        while True:
            try:
                states = {
                    resource_type: breaker.state
                    for resource_type, breaker in self.circuit_breakers.items()
                }
                logger.info("Circuit breaker states", extra={'states': states})
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Circuit breaker monitoring failed: {e}")
                await asyncio.sleep(5)

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(
            config.initial_delay * (config.exponential_base ** attempt),
            config.max_delay
        )
        jitter = config.jitter * (2 * (0.5 - time.time() % 1))  # Random jitter
        return max(0, delay + jitter)

    async def with_recovery(self,
                          operation: Callable[..., Awaitable[T]],
                          resource_type: ResourceType,
                          operation_type: OperationType,
                          fallback: Optional[Callable[..., Awaitable[T]]] = None,
                          *args,
                          **kwargs) -> T:
        """Execute operation with error recovery"""
        retry_config = self.retry_configs[resource_type.value]
        circuit_breaker = self.circuit_breakers[resource_type.value]
        
        if not circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker is open for {resource_type.value}")
            if fallback:
                return await fallback(*args, **kwargs)
            raise Exception(f"Circuit breaker is open for {resource_type.value}")
        
        last_error = None
        for attempt in range(retry_config.max_attempts):
            try:
                result = await operation(*args, **kwargs)
                circuit_breaker.record_success()
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Operation failed",
                    extra={
                        'resource_type': resource_type.value,
                        'operation_type': operation_type.value,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
                )
                
                circuit_breaker.record_failure()
                
                if attempt < retry_config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, retry_config)
                    await asyncio.sleep(delay)
                    continue
                
                if fallback:
                    try:
                        return await fallback(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback operation failed: {fallback_error}")
                        raise last_error
                
                raise last_error

    async def execute_db_operation(self,
                                 operation: Callable[..., Awaitable[T]],
                                 operation_type: OperationType,
                                 fallback: Optional[Callable[..., Awaitable[T]]] = None,
                                 *args,
                                 **kwargs) -> T:
        """Execute database operation with error recovery"""
        return await self.with_recovery(
            operation,
            ResourceType.DATABASE,
            operation_type,
            fallback,
            *args,
            **kwargs
        )

    async def execute_cache_operation(self,
                                    operation: Callable[..., Awaitable[T]],
                                    operation_type: OperationType,
                                    fallback: Optional[Callable[..., Awaitable[T]]] = None,
                                    *args,
                                    **kwargs) -> T:
        """Execute cache operation with error recovery"""
        return await self.with_recovery(
            operation,
            ResourceType.CACHE,
            operation_type,
            fallback,
            *args,
            **kwargs
        )

    async def execute_blockchain_operation(self,
                                         operation: Callable[..., Awaitable[T]],
                                         operation_type: OperationType,
                                         fallback: Optional[Callable[..., Awaitable[T]]] = None,
                                         *args,
                                         **kwargs) -> T:
        """Execute blockchain operation with error recovery"""
        return await self.with_recovery(
            operation,
            ResourceType.BLOCKCHAIN,
            operation_type,
            fallback,
            *args,
            **kwargs
        )

    async def execute_quantum_operation(self,
                                      operation: Callable[..., Awaitable[T]],
                                      operation_type: OperationType,
                                      fallback: Optional[Callable[..., Awaitable[T]]] = None,
                                      *args,
                                      **kwargs) -> T:
        """Execute quantum operation with error recovery"""
        return await self.with_recovery(
            operation,
            ResourceType.QUANTUM,
            operation_type,
            fallback,
            *args,
            **kwargs
        )

    def with_circuit_breaker(self, resource_type: ResourceType):
        """Decorator for adding circuit breaker to functions"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                circuit_breaker = self.circuit_breakers[resource_type.value]
                if not circuit_breaker.allow_request():
                    raise Exception(f"Circuit breaker is open for {resource_type.value}")
                try:
                    result = await func(*args, **kwargs)
                    circuit_breaker.record_success()
                    return result
                except Exception as e:
                    circuit_breaker.record_failure()
                    raise
            return wrapper
        return decorator

    def with_retry(self, resource_type: ResourceType):
        """Decorator for adding retry logic to functions"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                retry_config = self.retry_configs[resource_type.value]
                last_error = None
                
                for attempt in range(retry_config.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < retry_config.max_attempts - 1:
                            delay = self._calculate_delay(attempt, retry_config)
                            await asyncio.sleep(delay)
                            continue
                        raise
                
                if last_error:
                    raise last_error
                    
            return wrapper
        return decorator

# Global error recovery manager instance
error_recovery_manager = ErrorRecoveryManager()