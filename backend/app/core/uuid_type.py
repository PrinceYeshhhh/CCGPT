"""
UUID type compatibility for SQLite and PostgreSQL
"""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import TypeDecorator
import uuid


class UUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite"""
    
    impl = String(36)
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value) if isinstance(value, uuid.UUID) else value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value
