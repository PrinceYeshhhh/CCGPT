"""
Database configuration and session management with scaling optimizations
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import asyncio
from typing import Generator, List, Optional
from contextlib import asynccontextmanager
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# Enhanced PostgreSQL Database Configuration
def create_database_engine(url: str, is_read_replica: bool = False):
    """Create optimized database engine"""
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
        config['connect_args']['options'] += ' -c statement_timeout=30000'  # 30s timeout for reads
    
    return create_engine(url, **config)

# Primary write database
write_engine = create_database_engine(settings.DATABASE_URL, is_read_replica=False)
WriteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=write_engine)

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

# Enhanced Redis Configuration
class RedisManager:
    def __init__(self):
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
            decode_responses=True
        )
        
        self.redis_client = redis.Redis(connection_pool=self.connection_pool)
    
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
    
    async def health_check(self) -> dict:
        """Check database health"""
        health_status = {
            'write_db': False,
            'read_dbs': [],
            'overall': False
        }
        
        # Check write database
        try:
            with self.get_write_session() as db:
                db.execute(text("SELECT 1"))
                health_status['write_db'] = True
        except Exception as e:
            logger.error("Write database health check failed", error=str(e))
        
        # Check read databases
        for i, engine in enumerate(self.read_engines):
            try:
                with sessionmaker(bind=engine)() as db:
                    db.execute(text("SELECT 1"))
                    health_status['read_dbs'].append(True)
            except Exception as e:
                logger.error(f"Read database {i} health check failed", error=str(e))
                health_status['read_dbs'].append(False)
        
        health_status['overall'] = health_status['write_db'] and any(health_status['read_dbs'])
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
        # Create indexes for performance
        with db_manager.get_write_session() as db:
            # Document indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_workspace_status 
                ON documents(workspace_id, status)
            """))
            
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_workspace_uploaded 
                ON documents(workspace_id, uploaded_at)
            """))
            
            # Chunk indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_workspace_id 
                ON document_chunks(workspace_id)
            """))
            
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_document_workspace 
                ON document_chunks(document_id, workspace_id)
            """))
            
            # Chat session indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_sessions_workspace_created 
                ON chat_sessions(workspace_id, created_at)
            """))
            
            # Chat message indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_session_created 
                ON chat_messages(session_id, created_at)
            """))
            
            # Embedding indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_workspace_id 
                ON embeddings(workspace_id)
            """))
            
            # User indexes
            db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_workspace_id 
                ON users(workspace_id)
            """))
            
            db.commit()
            logger.info("Database indexes created successfully")
            
    except Exception as e:
        logger.error("Failed to initialize database indexes", error=str(e))
        raise
