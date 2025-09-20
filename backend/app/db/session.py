"""
Database session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis
from app.core.config import settings

# PostgreSQL Database
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.ENVIRONMENT == "development"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis Cache
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Redis dependency"""
    return redis_client
