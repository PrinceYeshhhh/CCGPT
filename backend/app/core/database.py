"""
Database configuration and session management with scaling optimizations
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import asyncio
import time
from typing import Generator, List, Optional
from contextlib import asynccontextmanager
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# Enhanced PostgreSQL Database Configuration
def create_database_engine(url: str, is_read_replica: bool = False):
    """Create optimized database engine"""
    # SQLite lightweight configuration for local/dev smoke tests
    if url.startswith("sqlite"):
        sqlite_config = {
            'echo': settings.ENVIRONMENT == "development",
            'connect_args': {
                'check_same_thread': False,
            },
        }
        return create_engine(url, **sqlite_config)

    # PostgreSQL optimized configuration
    config = {
        'pool_size': 50 if not is_read_replica else 30,
        'max_overflow': 30 if not is_read_replica else 20,
        'pool_timeout': 60,
        'pool_recycle': 1800,  # 30 minutes
        'pool_pre_ping': True,
        'echo': settings.ENVIRONMENT == "development",
        'connect_args': {
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
    
    if is_read_replica:
        options = config['connect_args']['options']
        if isinstance(options, str):
            config['connect_args']['options'] = options + ' -c statement_timeout=30000'  # 30s timeout for reads
    
    return create_engine(url, **config)

# Primary write database
write_engine = create_database_engine(settings.DATABASE_URL, is_read_replica=False)
# Expose a conventional name for compatibility with tests/imports
engine = write_engine
WriteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=write_engine)
# Backwards-compatibility alias expected by older tests/imports
SessionLocal = WriteSessionLocal

# Read replicas (if configured)
read_engines = []
if hasattr(settings, 'READ_REPLICA_URLS') and settings.READ_REPLICA_URLS:
    for replica_url in settings.READ_REPLICA_URLS:
        read_engine = create_database_engine(replica_url, is_read_replica=True)
        read_engines.append(read_engine)

# Fallback to write engine if no read replicas
if not read_engines:
    read_engines = [write_engine]

ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engines[0])

Base = declarative_base()

# Mock Redis client for when Redis is not available
class MockRedisClient:
    """Mock Redis client that does nothing when Redis is not available"""
    def ping(self):
        return True
    
    def get(self, key):
        return None
    
    def set(self, key, value, ex=None):
        return True
    
    def delete(self, key):
        return True
    
    def exists(self, key):
        return False
    
    def expire(self, key, time):
        return True
    
    def zadd(self, name, mapping):
        return 0
    
    def zremrangebyscore(self, name, min_score, max_score):
        return 0
    
    def zcard(self, name):
        return 0

# Enhanced Redis Configuration
class RedisManager:
    def __init__(self):
        self.redis_client = None
        self.redis_available = False
        
        try:
            self.redis_url = settings.REDIS_URL
            if settings.REDIS_PASSWORD:
                self.redis_url = self.redis_url.replace("redis://", f"redis://:{settings.REDIS_PASSWORD}@")
            
            # Connection pool configuration
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=100,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                },
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                decode_responses=True
            )
            
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            # Test connection (pool enforces socket timeouts)
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using fallback: {str(e)}")
            self.redis_available = False
            self.redis_client = MockRedisClient()
    
    def get_client(self):
        return self.redis_client
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False

redis_manager = RedisManager()

# Database connection management
class DatabaseManager:
    def __init__(self):
        self.write_engine = write_engine
        self.read_engines = read_engines
        self.current_read_engine = 0
        self._read_engines_lock = asyncio.Lock()
        self._connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'failed_connections': 0,
            'last_health_check': None
        }
    
    def get_write_session(self):
        """Get write database session"""
        return WriteSessionLocal()
    
    def get_read_session(self):
        """Get read database session (round-robin)"""
        return ReadSessionLocal()
    
    async def get_read_session_async(self):
        """Get read database session with load balancing"""
        async with self._read_engines_lock:
            engine = self.read_engines[self.current_read_engine]
            self.current_read_engine = (self.current_read_engine + 1) % len(self.read_engines)
        
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    
    def get_connection_stats(self) -> dict:
        """Get current connection pool statistics"""
        try:
            # Get write engine stats
            write_pool = self.write_engine.pool
            stats = {
                'write_db': {
                    'size': write_pool.size(),
                    'checked_in': write_pool.checkedin(),
                    'checked_out': write_pool.checkedout(),
                    'overflow': write_pool.overflow(),
                    'invalid': write_pool.invalid()
                },
                'read_dbs': []
            }
            
            # Get read engine stats
            for i, engine in enumerate(self.read_engines):
                read_pool = engine.pool
                stats['read_dbs'].append({
                    'index': i,
                    'size': read_pool.size(),
                    'checked_in': read_pool.checkedin(),
                    'checked_out': read_pool.checkedout(),
                    'overflow': read_pool.overflow(),
                    'invalid': read_pool.invalid()
                })
            
            return stats
        except Exception as e:
            logger.error("Failed to get connection stats", error=str(e))
            return {}
    
    def cleanup_connections(self):
        """Clean up invalid connections and reset pool"""
        try:
            # Cleanup write engine
            write_pool = self.write_engine.pool
            invalid_count = write_pool.invalid()
            if invalid_count > 0:
                logger.warning(f"Cleaning up {invalid_count} invalid write connections")
                write_pool.recreate()
            
            # Cleanup read engines
            for i, engine in enumerate(self.read_engines):
                read_pool = engine.pool
                invalid_count = read_pool.invalid()
                if invalid_count > 0:
                    logger.warning(f"Cleaning up {invalid_count} invalid read connections from engine {i}")
                    read_pool.recreate()
            
            logger.info("Connection cleanup completed")
        except Exception as e:
            logger.error("Connection cleanup failed", error=str(e))
    
    def monitor_connections(self):
        """Monitor connection health and perform maintenance"""
        try:
            stats = self.get_connection_stats()
            
            # Check for connection issues
            write_db = stats.get('write_db', {})
            if write_db.get('invalid', 0) > 5:  # More than 5 invalid connections
                logger.warning("High number of invalid write connections detected")
                self.cleanup_connections()
            
            # Check read databases
            for read_db in stats.get('read_dbs', []):
                if read_db.get('invalid', 0) > 5:
                    logger.warning(f"High number of invalid read connections detected in engine {read_db.get('index', 'unknown')}")
                    self.cleanup_connections()
                    break
            
            # Update metrics
            from app.utils.metrics import metrics_collector
            total_active = write_db.get('checked_out', 0) + sum(rd.get('checked_out', 0) for rd in stats.get('read_dbs', []))
            total_idle = write_db.get('checked_in', 0) + sum(rd.get('checked_in', 0) for rd in stats.get('read_dbs', []))
            metrics_collector.set_database_connections(total_active, total_idle)
            
        except Exception as e:
            logger.error("Connection monitoring failed", error=str(e))
    
    async def health_check(self) -> dict:
        """Check database health with detailed diagnostics"""
        health_status = {
            'write_db': False,
            'read_dbs': [],
            'overall': False,
            'connection_stats': {},
            'response_times': {}
        }
        
        # Check write database
        try:
            start_time = time.time()
            with self.get_write_session() as db:
                db.execute(text("SELECT 1"))
                response_time = (time.time() - start_time) * 1000
                health_status['write_db'] = True
                health_status['response_times']['write_db'] = response_time
        except Exception as e:
            logger.error("Write database health check failed", error=str(e))
            health_status['write_db'] = False
        
        # Check read databases
        for i, engine in enumerate(self.read_engines):
            try:
                start_time = time.time()
                with sessionmaker(bind=engine)() as db:
                    db.execute(text("SELECT 1"))
                    response_time = (time.time() - start_time) * 1000
                    health_status['read_dbs'].append(True)
                    health_status['response_times'][f'read_db_{i}'] = response_time
            except Exception as e:
                logger.error(f"Read database {i} health check failed", error=str(e))
                health_status['read_dbs'].append(False)
        
        # Get connection statistics
        health_status['connection_stats'] = self.get_connection_stats()
        
        # Determine overall health
        health_status['overall'] = health_status['write_db'] and any(health_status['read_dbs'])
        
        # Update last health check time
        self._connection_stats['last_health_check'] = time.time()
        
        return health_status

db_manager = DatabaseManager()

# Dependency functions
def get_db() -> Generator:
    """Database dependency for write operations"""
    db = db_manager.get_write_session()
    try:
        yield db
    finally:
        db.close()

def get_read_db() -> Generator:
    """Database dependency for read operations"""
    db = db_manager.get_read_session()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def get_async_read_db():
    """Async database dependency for read operations"""
    db = await db_manager.get_read_session_async()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Redis dependency"""
    return redis_manager.get_client()

# Database initialization and optimization
async def initialize_database():
    """Initialize database with optimizations"""
    try:
        # Skip Postgres-specific concurrent index creation on SQLite
        if settings.DATABASE_URL.startswith("sqlite"):
            logger.info("SQLite detected; skipping concurrent index creation")
            return
        # Create indexes for performance
        # CREATE INDEX CONCURRENTLY cannot run inside a transaction; use autocommit
        with db_manager.get_write_session().bind.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")

            # Document indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_documents_workspace_status ON documents(workspace_id, status)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_documents_workspace_uploaded ON documents(workspace_id, uploaded_at)"
            ))

            # Chunk indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_chunks_workspace_id ON document_chunks(workspace_id)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_chunks_document_workspace ON document_chunks(document_id, workspace_id)"
            ))

            # Chat session indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_workspace_created ON chat_sessions(workspace_id, created_at)"
            ))

            # Chat message indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at)"
            ))

            # User indexes
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_users_workspace_id ON users(workspace_id)"
            ))

            logger.info("Database indexes ensured successfully")
            
    except Exception as e:
        logger.error("Failed to initialize database indexes", error=str(e))
        raise
