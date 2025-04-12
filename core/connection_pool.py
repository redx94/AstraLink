"""
Connection Pool Manager - Manages database and service connection pools
"""
import asyncio
from typing import Dict, Any, Optional, Callable, AsyncGenerator
import aioredis
import aiomysql
import asyncpg
from aiohttp import ClientSession, ClientTimeout
import time
from ..logging_config import get_logger
from ..config import config_manager

logger = get_logger(__name__)

class ConnectionPool:
    """Base connection pool class"""
    def __init__(self, pool_config: Dict[str, Any]):
        self.config = pool_config
        self.min_size = pool_config.get('min_size', 5)
        self.max_size = pool_config.get('max_size', 20)
        self.timeout = pool_config.get('timeout', 30)
        self.retry_limit = pool_config.get('retry_limit', 3)
        self.pool = None
        self._last_connection_time = {}
        self._connection_attempts = {}
        self._in_use_connections = set()
        self._available_connections = set()
        self._cleanup_task = None

    async def initialize(self):
        """Initialize the connection pool"""
        raise NotImplementedError

    async def get_connection(self):
        """Get a connection from the pool"""
        raise NotImplementedError

    async def release_connection(self, connection):
        """Release a connection back to the pool"""
        raise NotImplementedError

    async def close(self):
        """Close the connection pool"""
        raise NotImplementedError

class PostgresPool(ConnectionPool):
    """PostgreSQL connection pool"""
    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.timeout
            )
            logger.info("Initialized PostgreSQL connection pool")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def get_connection(self):
        """Get a PostgreSQL connection with retry logic"""
        for attempt in range(self.retry_limit):
            try:
                conn = await self.pool.acquire()
                self._in_use_connections.add(conn)
                self._last_connection_time[conn] = time.time()
                return conn
            except Exception as e:
                if attempt == self.retry_limit - 1:
                    logger.error(f"Failed to get PostgreSQL connection after {self.retry_limit} attempts: {e}")
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def release_connection(self, connection):
        """Release a PostgreSQL connection"""
        try:
            self._in_use_connections.remove(connection)
            self._available_connections.add(connection)
            await self.pool.release(connection)
        except Exception as e:
            logger.error(f"Failed to release PostgreSQL connection: {e}")

    async def close(self):
        """Close PostgreSQL connection pool"""
        try:
            await self.pool.close()
            logger.info("Closed PostgreSQL connection pool")
        except Exception as e:
            logger.error(f"Failed to close PostgreSQL pool: {e}")

class RedisPool(ConnectionPool):
    """Redis connection pool"""
    async def initialize(self):
        try:
            self.pool = await aioredis.create_redis_pool(
                f"redis://{self.config['host']}:{self.config['port']}",
                password=self.config.get('password'),
                minsize=self.min_size,
                maxsize=self.max_size,
                timeout=self.timeout
            )
            logger.info("Initialized Redis connection pool")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise

    async def get_connection(self):
        """Get a Redis connection"""
        for attempt in range(self.retry_limit):
            try:
                conn = await self.pool.acquire()
                self._in_use_connections.add(conn)
                self._last_connection_time[conn] = time.time()
                return conn
            except Exception as e:
                if attempt == self.retry_limit - 1:
                    logger.error(f"Failed to get Redis connection after {self.retry_limit} attempts: {e}")
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def release_connection(self, connection):
        """Release a Redis connection"""
        try:
            self._in_use_connections.remove(connection)
            self._available_connections.add(connection)
            await self.pool.release(connection)
        except Exception as e:
            logger.error(f"Failed to release Redis connection: {e}")

    async def close(self):
        """Close Redis connection pool"""
        try:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Closed Redis connection pool")
        except Exception as e:
            logger.error(f"Failed to close Redis pool: {e}")

class HTTPPool(ConnectionPool):
    """HTTP client session pool"""
    def __init__(self, pool_config: Dict[str, Any]):
        super().__init__(pool_config)
        self._sessions = set()

    async def initialize(self):
        """Initialize HTTP session pool"""
        try:
            for _ in range(self.min_size):
                session = ClientSession(
                    timeout=ClientTimeout(total=self.timeout),
                    headers=self.config.get('headers', {})
                )
                self._available_connections.add(session)
                self._sessions.add(session)
            logger.info("Initialized HTTP session pool")
        except Exception as e:
            logger.error(f"Failed to initialize HTTP session pool: {e}")
            raise

    async def get_connection(self):
        """Get an HTTP session"""
        for attempt in range(self.retry_limit):
            try:
                if not self._available_connections and len(self._sessions) < self.max_size:
                    # Create new session if under max_size
                    session = ClientSession(
                        timeout=ClientTimeout(total=self.timeout),
                        headers=self.config.get('headers', {})
                    )
                    self._sessions.add(session)
                    self._available_connections.add(session)

                if self._available_connections:
                    session = self._available_connections.pop()
                    self._in_use_connections.add(session)
                    self._last_connection_time[session] = time.time()
                    return session

                # Wait for a session to become available
                await asyncio.sleep(0.1)
                continue

            except Exception as e:
                if attempt == self.retry_limit - 1:
                    logger.error(f"Failed to get HTTP session after {self.retry_limit} attempts: {e}")
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

    async def release_connection(self, session):
        """Release an HTTP session"""
        try:
            self._in_use_connections.remove(session)
            self._available_connections.add(session)
        except Exception as e:
            logger.error(f"Failed to release HTTP session: {e}")

    async def close(self):
        """Close HTTP session pool"""
        try:
            for session in self._sessions:
                await session.close()
            self._sessions.clear()
            self._available_connections.clear()
            self._in_use_connections.clear()
            logger.info("Closed HTTP session pool")
        except Exception as e:
            logger.error(f"Failed to close HTTP session pool: {e}")

class ConnectionPoolManager:
    """Manages multiple connection pools"""
    def __init__(self):
        self.config = config_manager.get_value('connections', {})
        self.pools: Dict[str, ConnectionPool] = {}
        self._maintenance_task = None
        self._initialize_pools()

    def _initialize_pools(self):
        """Initialize connection pools from configuration"""
        try:
            # Initialize PostgreSQL pools
            for name, config in self.config.get('postgres', {}).items():
                self.pools[f'postgres_{name}'] = PostgresPool(config)

            # Initialize Redis pools
            for name, config in self.config.get('redis', {}).items():
                self.pools[f'redis_{name}'] = RedisPool(config)

            # Initialize HTTP pools
            for name, config in self.config.get('http', {}).items():
                self.pools[f'http_{name}'] = HTTPPool(config)

            # Start maintenance task
            self._maintenance_task = asyncio.create_task(self._pool_maintenance_loop())

        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise

    async def start(self):
        """Start all connection pools"""
        try:
            await asyncio.gather(*(
                pool.initialize()
                for pool in self.pools.values()
            ))
            logger.info("All connection pools started")
        except Exception as e:
            logger.error(f"Failed to start connection pools: {e}")
            raise

    async def stop(self):
        """Stop all connection pools"""
        try:
            if self._maintenance_task:
                self._maintenance_task.cancel()
                try:
                    await self._maintenance_task
                except asyncio.CancelledError:
                    pass

            await asyncio.gather(*(
                pool.close()
                for pool in self.pools.values()
            ))
            logger.info("All connection pools stopped")
        except Exception as e:
            logger.error(f"Failed to stop connection pools: {e}")

    async def get_connection(self, pool_name: str):
        """Get a connection from specified pool"""
        try:
            pool = self.pools[pool_name]
            return await pool.get_connection()
        except KeyError:
            raise ValueError(f"Pool not found: {pool_name}")
        except Exception as e:
            logger.error(f"Failed to get connection from pool {pool_name}: {e}")
            raise

    async def release_connection(self, pool_name: str, connection):
        """Release a connection back to specified pool"""
        try:
            pool = self.pools[pool_name]
            await pool.release_connection(connection)
        except KeyError:
            raise ValueError(f"Pool not found: {pool_name}")
        except Exception as e:
            logger.error(f"Failed to release connection to pool {pool_name}: {e}")

    async def _pool_maintenance_loop(self):
        """Periodic pool maintenance"""
        while True:
            try:
                current_time = time.time()
                
                for pool_name, pool in self.pools.items():
                    # Check for stale connections
                    stale_connections = [
                        conn for conn in pool._in_use_connections
                        if current_time - pool._last_connection_time.get(conn, 0) > pool.timeout
                    ]
                    
                    # Release stale connections
                    for conn in stale_connections:
                        logger.warning(f"Releasing stale connection in pool {pool_name}")
                        await pool.release_connection(conn)
                    
                    # Log pool statistics
                    logger.debug(
                        f"Pool {pool_name} stats: "
                        f"in_use={len(pool._in_use_connections)}, "
                        f"available={len(pool._available_connections)}"
                    )
                
                await asyncio.sleep(60)  # Run maintenance every minute
                
            except Exception as e:
                logger.error(f"Pool maintenance failed: {e}")
                await asyncio.sleep(5)

    async def connection_context(self, pool_name: str) -> AsyncGenerator[Any, None]:
        """Context manager for automatic connection handling"""
        connection = None
        try:
            connection = await self.get_connection(pool_name)
            yield connection
        finally:
            if connection:
                await self.release_connection(pool_name, connection)

# Global connection pool manager instance
pool_manager = ConnectionPoolManager()