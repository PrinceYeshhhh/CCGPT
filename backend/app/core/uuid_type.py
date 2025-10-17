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
            # Accept strings or UUIDs; generate a UUID if value is invalid
            if isinstance(value, uuid.UUID):
                return str(value)
            try:
                # Validate/normalize string UUIDs
                return str(uuid.UUID(str(value)))
            except Exception:
                # If invalid, return original string to avoid unintended changes
                return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            # Attempt to parse UUID strings; if invalid, return original string
            try:
                return uuid.UUID(str(value))
            except Exception:
                return value
