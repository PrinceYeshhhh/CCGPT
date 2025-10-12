# Database Query Optimization Service
# Advanced query optimization, connection pooling, and performance monitoring

import time
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import text, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select
import structlog
from app.core.database import db_manager, get_db
from app.core.config import settings
from app.services.cache_service import QueryCache, cache_service

logger = structlog.get_logger()

class QueryPerformanceMonitor:
    """Monitor and track query performance"""
    
    def __init__(self):
        self.slow_queries = []
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second
    
    def record_query(self, query: str, duration: float, params: Dict = None):
        """Record query performance"""
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                "query": query,
                "duration": duration,
                "params": params,
                "timestamp": time.time()
            })
            
            logger.warning(
                "Slow query detected",
                query=query[:200],
                duration=duration,
                params=params
            )
        
        # Update stats
        query_hash = hash(query)
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "query": query,
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "max_duration": 0
            }
        
        stats = self.query_stats[query_hash]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        stats["max_duration"] = max(stats["max_duration"], duration)
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent slow queries"""
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True
        )[:limit]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        if not self.query_stats:
            return {}
        
        total_queries = sum(stats["count"] for stats in self.query_stats.values())
        total_duration = sum(stats["total_duration"] for stats in self.query_stats.values())
        
        return {
            "total_queries": total_queries,
            "total_duration": total_duration,
            "avg_duration": total_duration / total_queries if total_queries > 0 else 0,
            "slow_queries_count": len(self.slow_queries),
            "unique_queries": len(self.query_stats),
            "top_slow_queries": self.get_slow_queries(5)
        }

# Global query monitor
query_monitor = QueryPerformanceMonitor()

class OptimizedQueryBuilder:
    """Builder for optimized database queries"""
    
    def __init__(self, session: Session):
        self.session = session
        self.query = None
        self.use_cache = True
        self.cache_ttl = 300
    
    def select(self, *columns):
        """Start a SELECT query"""
        self.query = self.session.query(*columns)
        return self
    
    def from_table(self, table):
        """Set the main table"""
        if self.query is None:
            self.query = self.session.query(table)
        return self
    
    def where(self, *conditions):
        """Add WHERE conditions"""
        if self.query is not None:
            self.query = self.query.filter(*conditions)
        return self
    
    def join(self, table, condition=None, isouter=False):
        """Add JOIN"""
        if self.query is not None:
            if isouter:
                self.query = self.query.outerjoin(table, condition)
            else:
                self.query = self.query.join(table, condition)
        return self
    
    def order_by(self, *columns):
        """Add ORDER BY"""
        if self.query is not None:
            self.query = self.query.order_by(*columns)
        return self
    
    def limit(self, count: int):
        """Add LIMIT"""
        if self.query is not None:
            self.query = self.query.limit(count)
        return self
    
    def offset(self, count: int):
        """Add OFFSET"""
        if self.query is not None:
            self.query = self.query.offset(count)
        return self
    
    def group_by(self, *columns):
        """Add GROUP BY"""
        if self.query is not None:
            self.query = self.query.group_by(*columns)
        return self
    
    def having(self, *conditions):
        """Add HAVING"""
        if self.query is not None:
            self.query = self.query.having(*conditions)
        return self
    
    def with_entities(self, *entities):
        """Add specific entities to select"""
        if self.query is not None:
            self.query = self.query.with_entities(*entities)
        return self
    
    def options(self, *options):
        """Add query options (eager loading, etc.)"""
        if self.query is not None:
            self.query = self.query.options(*options)
        return self
    
    def cache(self, ttl: int = 300):
        """Enable caching for this query"""
        self.use_cache = True
        self.cache_ttl = ttl
        return self
    
    def no_cache(self):
        """Disable caching for this query"""
        self.use_cache = False
        return self
    
    async def execute(self, cache_key: Optional[str] = None) -> Any:
        """Execute the query with performance monitoring"""
        if self.query is None:
            raise ValueError("No query defined")
        
        start_time = time.time()
        
        try:
            # Try cache first if enabled
            if self.use_cache and cache_key:
                cached_result = await cache_service.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute query
            result = self.query.all()
            
            # Record performance
            duration = time.time() - start_time
            query_monitor.record_query(
                str(self.query.statement),
                duration,
                {"cache_key": cache_key}
            )
            
            # Cache result if enabled
            if self.use_cache and cache_key:
                await cache_service.set(cache_key, result, self.cache_ttl)
            
            return result
            
        except SQLAlchemyError as e:
            duration = time.time() - start_time
            logger.error(
                "Query execution failed",
                query=str(self.query.statement),
                duration=duration,
                error=str(e)
            )
            raise
    
    def first(self):
        """Execute query and return first result"""
        if self.query is None:
            raise ValueError("No query defined")
        
        start_time = time.time()
        
        try:
            result = self.query.first()
            
            duration = time.time() - start_time
            query_monitor.record_query(
                str(self.query.statement),
                duration
            )
            
            return result
            
        except SQLAlchemyError as e:
            duration = time.time() - start_time
            logger.error(
                "Query execution failed",
                query=str(self.query.statement),
                duration=duration,
                error=str(e)
            )
            raise
    
    def count(self):
        """Execute query and return count"""
        if self.query is None:
            raise ValueError("No query defined")
        
        start_time = time.time()
        
        try:
            result = self.query.count()
            
            duration = time.time() - start_time
            query_monitor.record_query(
                str(self.query.statement),
                duration
            )
            
            return result
            
        except SQLAlchemyError as e:
            duration = time.time() - start_time
            logger.error(
                "Query execution failed",
                query=str(self.query.statement),
                duration=duration,
                error=str(e)
            )
            raise

class DatabaseOptimizer:
    """Database optimization service"""
    
    def __init__(self):
        self.connection_pool_stats = {}
        self.index_recommendations = []
    
    async def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance and provide recommendations"""
        stats = query_monitor.get_query_stats()
        slow_queries = query_monitor.get_slow_queries(10)
        
        recommendations = []
        
        # Analyze slow queries for common patterns
        for query_data in slow_queries:
            query = query_data["query"]
            
            # Check for missing indexes
            if "WHERE" in query.upper() and "ORDER BY" in query.upper():
                recommendations.append({
                    "type": "missing_index",
                    "query": query[:100],
                    "suggestion": "Consider adding composite index on WHERE and ORDER BY columns"
                })
            
            # Check for N+1 queries
            if query.count("SELECT") > 1:
                recommendations.append({
                    "type": "n_plus_one",
                    "query": query[:100],
                    "suggestion": "Consider using eager loading or batch loading"
                })
            
            # Check for full table scans
            if "WHERE" not in query.upper() and "JOIN" not in query.upper():
                recommendations.append({
                    "type": "full_table_scan",
                    "query": query[:100],
                    "suggestion": "Add WHERE clause or LIMIT to avoid full table scan"
                })
        
        return {
            "performance_stats": stats,
            "slow_queries": slow_queries,
            "recommendations": recommendations
        }
    
    async def optimize_connection_pool(self) -> Dict[str, Any]:
        """Analyze and optimize connection pool settings"""
        stats = db_manager.get_connection_stats()
        
        recommendations = []
        
        # Check connection pool utilization
        write_pool = stats.get("write_db", {})
        if write_pool:
            size = write_pool.get("size", 0)
            checked_out = write_pool.get("checked_out", 0)
            utilization = checked_out / size if size > 0 else 0
            
            if utilization > 0.8:
                recommendations.append({
                    "type": "pool_size",
                    "current": size,
                    "suggestion": f"Increase pool size from {size} to {int(size * 1.5)}"
                })
            
            if utilization < 0.2 and size > 10:
                recommendations.append({
                    "type": "pool_size",
                    "current": size,
                    "suggestion": f"Decrease pool size from {size} to {int(size * 0.7)}"
                })
        
        return {
            "current_stats": stats,
            "recommendations": recommendations
        }
    
    async def suggest_indexes(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Suggest database indexes based on query patterns"""
        suggestions = []
        
        # Common index suggestions based on application patterns
        common_indexes = [
            {
                "table": "documents",
                "columns": ["workspace_id", "status", "uploaded_at"],
                "type": "composite",
                "reason": "Frequent filtering by workspace, status, and date range"
            },
            {
                "table": "chat_sessions",
                "columns": ["workspace_id", "created_at"],
                "type": "composite",
                "reason": "Frequent ordering by creation date within workspace"
            },
            {
                "table": "chat_messages",
                "columns": ["session_id", "created_at"],
                "type": "composite",
                "reason": "Frequent ordering by creation date within session"
            },
            {
                "table": "users",
                "columns": ["workspace_id", "email"],
                "type": "composite",
                "reason": "Frequent lookups by workspace and email"
            },
            {
                "table": "embed_codes",
                "columns": ["workspace_id", "client_api_key"],
                "type": "composite",
                "reason": "Frequent lookups by API key within workspace"
            }
        ]
        
        return suggestions + common_indexes
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with db_manager.get_read_session() as db:
                # Table sizes
                table_sizes = db.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)).fetchall()
                
                # Index usage
                index_usage = db.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """)).fetchall()
                
                # Connection stats
                connection_stats = db.execute(text("""
                    SELECT 
                        state,
                        count(*) as count
                    FROM pg_stat_activity
                    GROUP BY state
                """)).fetchall()
                
                return {
                    "table_sizes": [dict(row._mapping) for row in table_sizes],
                    "index_usage": [dict(row._mapping) for row in index_usage],
                    "connection_stats": [dict(row._mapping) for row in connection_stats],
                    "query_performance": query_monitor.get_query_stats()
                }
                
        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            return {}

# Global database optimizer
db_optimizer = DatabaseOptimizer()

# Query optimization utilities
class QueryUtils:
    """Utility functions for query optimization"""
    
    @staticmethod
    def build_workspace_filter(workspace_id: str, table_alias: str = None):
        """Build workspace filter for multi-tenant queries"""
        if table_alias:
            return getattr(table_alias, "workspace_id") == workspace_id
        return text("workspace_id = :workspace_id")
    
    @staticmethod
    def build_date_range_filter(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        date_column: str = "created_at",
        table_alias: str = None
    ):
        """Build date range filter"""
        conditions = []
        
        if start_date:
            if table_alias:
                conditions.append(getattr(table_alias, date_column) >= start_date)
            else:
                conditions.append(text(f"{date_column} >= :start_date"))
        
        if end_date:
            if table_alias:
                conditions.append(getattr(table_alias, date_column) <= end_date)
            else:
                conditions.append(text(f"{date_column} <= :end_date"))
        
        return and_(*conditions) if conditions else None
    
    @staticmethod
    def build_pagination_query(
        query,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ):
        """Build paginated query"""
        offset = (page - 1) * page_size
        
        # Add ordering
        if order_direction.lower() == "desc":
            query = query.order_by(desc(order_by))
        else:
            query = query.order_by(asc(order_by))
        
        # Add pagination
        query = query.offset(offset).limit(page_size)
        
        return query
    
    @staticmethod
    def build_search_filter(
        search_term: str,
        search_columns: List[str],
        table_alias: str = None
    ):
        """Build text search filter"""
        if not search_term:
            return None
        
        search_conditions = []
        
        for column in search_columns:
            if table_alias:
                search_conditions.append(
                    getattr(table_alias, column).ilike(f"%{search_term}%")
                )
            else:
                search_conditions.append(
                    text(f"{column} ILIKE :search_term")
                )
        
        return or_(*search_conditions)

# Cached query decorators
def cached_query(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching query results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                cache_key = f"query:{func.__name__}:{hash(str(key_data))}"
            
            # Try cache first
            result = await cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute query
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def query_performance_monitor(func):
    """Decorator for monitoring query performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            query_monitor.record_query(
                func.__name__,
                duration,
                {"args": str(args), "kwargs": str(kwargs)}
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Query function failed",
                func=func.__name__,
                duration=duration,
                error=str(e)
            )
            raise
    
    return wrapper
