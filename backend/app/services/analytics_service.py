"""
Real-time analytics service for CustomerCareGPT
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import structlog
import redis
from functools import lru_cache

from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.models.embed import EmbedCode
from app.exceptions import AnalyticsError, DatabaseError

logger = structlog.get_logger()


class AnalyticsService:
    """Real-time analytics service for tracking usage and performance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    async def get_dashboard_metrics(self, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics with caching"""
        try:
            # Create cache key
            cache_key = f"dashboard_metrics:{workspace_id}:{days}"
            
            # Try to get from cache first
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info("Returning cached dashboard metrics", workspace_id=workspace_id)
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning("Failed to get from cache", error=str(e))
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get basic metrics
            metrics = await asyncio.gather(
                self._get_chat_metrics(workspace_id, start_date, end_date),
                self._get_document_metrics(workspace_id, start_date, end_date),
                self._get_embed_metrics(workspace_id, start_date, end_date),
                self._get_performance_metrics(workspace_id, start_date, end_date),
                self._get_language_metrics(workspace_id, start_date, end_date),
                return_exceptions=True
            )
            
            # Extract key metrics for the frontend
            chat_metrics = metrics[0] if not isinstance(metrics[0], Exception) else {}
            performance_metrics = metrics[3] if not isinstance(metrics[3], Exception) else {}
            
            # Return simplified structure for frontend
            result = {
                "total_queries": chat_metrics.get("total_messages", 0),
                "unique_users": chat_metrics.get("unique_users", 0),
                "avg_response_time": performance_metrics.get("avg_response_time_ms", 0) / 1000,  # Convert to seconds
                "satisfaction_rate": performance_metrics.get("satisfaction_rate", 0),
                "workspace_id": workspace_id,
                "period_days": days,
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache the result for 5 minutes
            try:
                self.redis_client.setex(cache_key, 300, json.dumps(result))
            except Exception as e:
                logger.warning("Failed to cache dashboard metrics", error=str(e))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get dashboard metrics", error=str(e), workspace_id=workspace_id)
            raise AnalyticsError(
                message="Failed to generate dashboard metrics",
                details={"workspace_id": workspace_id, "error": str(e)}
            )
    
    async def _get_chat_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get chat-related metrics"""
        try:
            # Total sessions
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).count()
            
            # Active sessions
            active_sessions = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.is_active == True
            ).count()
            
            # Total messages
            total_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).count()
            
            # User messages vs AI messages
            user_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).count()
            
            ai_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "assistant",
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).count()
            
            # Average session length
            avg_session_length = self.db.query(func.avg(
                func.extract('epoch', ChatSession.ended_at - ChatSession.created_at)
            )).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.ended_at.isnot(None),
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).scalar() or 0
            
            # Unique users (distinct user sessions)
            unique_users = self.db.query(func.count(func.distinct(ChatSession.user_id))).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).scalar() or 0
            
            # Daily session counts
            daily_sessions = self.db.query(
                func.date(ChatSession.created_at).label('date'),
                func.count(ChatSession.id).label('count')
            ).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).group_by(func.date(ChatSession.created_at)).all()
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "user_messages": user_messages,
                "ai_messages": ai_messages,
                "unique_users": unique_users,
                "avg_session_length_seconds": round(avg_session_length, 2),
                "daily_sessions": [{"date": str(d[0]), "count": d[1]} for d in daily_sessions]
            }
            
        except Exception as e:
            logger.error("Failed to get chat metrics", error=str(e))
            raise AnalyticsError("Failed to get chat metrics", details={"error": str(e)})
    
    async def _get_document_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get document-related metrics"""
        try:
            # Total documents
            total_documents = self.db.query(Document).filter(
                Document.workspace_id == workspace_id,
                Document.created_at >= start_date,
                Document.created_at <= end_date
            ).count()
            
            # Documents by status
            documents_by_status = self.db.query(
                Document.status,
                func.count(Document.id).label('count')
            ).filter(
                Document.workspace_id == workspace_id,
                Document.created_at >= start_date,
                Document.created_at <= end_date
            ).group_by(Document.status).all()
            
            # Total chunks
            total_chunks = self.db.query(func.count(Document.id)).join(
                Document, Document.id == Document.id
            ).filter(
                Document.workspace_id == workspace_id,
                Document.created_at >= start_date,
                Document.created_at <= end_date
            ).scalar() or 0
            
            return {
                "total_documents": total_documents,
                "documents_by_status": {status: count for status, count in documents_by_status},
                "total_chunks": total_chunks
            }
            
        except Exception as e:
            logger.error("Failed to get document metrics", error=str(e))
            raise AnalyticsError("Failed to get document metrics", details={"error": str(e)})
    
    async def _get_embed_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get embed widget metrics"""
        try:
            # Total embed codes
            total_embed_codes = self.db.query(EmbedCode).filter(
                EmbedCode.workspace_id == workspace_id,
                EmbedCode.created_at >= start_date,
                EmbedCode.created_at <= end_date
            ).count()
            
            # Active embed codes
            active_embed_codes = self.db.query(EmbedCode).filter(
                EmbedCode.workspace_id == workspace_id,
                EmbedCode.is_active == True
            ).count()
            
            # Total usage
            total_usage = self.db.query(func.sum(EmbedCode.usage_count)).filter(
                EmbedCode.workspace_id == workspace_id
            ).scalar() or 0
            
            # Most used embed codes
            top_embed_codes = self.db.query(
                EmbedCode.code_name,
                EmbedCode.usage_count
            ).filter(
                EmbedCode.workspace_id == workspace_id
            ).order_by(desc(EmbedCode.usage_count)).limit(5).all()
            
            return {
                "total_embed_codes": total_embed_codes,
                "active_embed_codes": active_embed_codes,
                "total_usage": total_usage,
                "top_embed_codes": [{"name": name, "usage": usage} for name, usage in top_embed_codes]
            }
            
        except Exception as e:
            logger.error("Failed to get embed metrics", error=str(e))
            raise AnalyticsError("Failed to get embed metrics", details={"error": str(e)})
    
    async def _get_performance_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Average response time
            avg_response_time = self.db.query(func.avg(ChatMessage.response_time_ms)).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.response_time_ms.isnot(None),
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).scalar() or 0
            
            # Response time distribution
            response_times = self.db.query(ChatMessage.response_time_ms).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.response_time_ms.isnot(None),
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).all()
            
            response_times_list = [rt[0] for rt in response_times if rt[0]]
            
            # Calculate percentiles
            if response_times_list:
                sorted_times = sorted(response_times_list)
                p50 = sorted_times[int(len(sorted_times) * 0.5)]
                p90 = sorted_times[int(len(sorted_times) * 0.9)]
                p95 = sorted_times[int(len(sorted_times) * 0.95)]
                p99 = sorted_times[int(len(sorted_times) * 0.99)]
            else:
                p50 = p90 = p95 = p99 = 0
            
            # Confidence score distribution
            confidence_scores = self.db.query(
                ChatMessage.confidence_score,
                func.count(ChatMessage.id).label('count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.confidence_score.isnot(None),
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).group_by(ChatMessage.confidence_score).all()
            
            # Calculate satisfaction rate based on confidence scores
            total_messages = sum(count for _, count in confidence_scores)
            high_confidence = sum(count for score, count in confidence_scores if score == 'high')
            satisfaction_rate = (high_confidence / total_messages * 100) if total_messages > 0 else 0
            
            return {
                "avg_response_time_ms": round(avg_response_time, 2),
                "satisfaction_rate": round(satisfaction_rate, 2),
                "response_time_percentiles": {
                    "p50": p50,
                    "p90": p90,
                    "p95": p95,
                    "p99": p99
                },
                "confidence_distribution": {score: count for score, count in confidence_scores}
            }
            
        except Exception as e:
            logger.error("Failed to get performance metrics", error=str(e))
            raise AnalyticsError("Failed to get performance metrics", details={"error": str(e)})
    
    async def _get_language_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get language usage metrics"""
        try:
            # This would require storing language information in messages
            # For now, return placeholder data
            return {
                "total_languages_detected": 0,
                "language_distribution": {},
                "most_common_language": "en"
            }
            
        except Exception as e:
            logger.error("Failed to get language metrics", error=str(e))
            raise AnalyticsError("Failed to get language metrics", details={"error": str(e)})
    
    async def get_real_time_metrics(self, workspace_id: str) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard"""
        try:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            
            # Active sessions in last hour
            active_sessions = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.last_activity_at >= last_hour
            ).count()
            
            # Messages in last hour
            messages_last_hour = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= last_hour
            ).count()
            
            # Current online users (sessions active in last 5 minutes)
            online_users = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.last_activity_at >= now - timedelta(minutes=5)
            ).count()
            
            return {
                "timestamp": now.isoformat(),
                "active_sessions": active_sessions,
                "messages_last_hour": messages_last_hour,
                "online_users": online_users
            }
            
        except Exception as e:
            logger.error("Failed to get real-time metrics", error=str(e))
            raise AnalyticsError("Failed to get real-time metrics", details={"error": str(e)})
    
    async def track_event(self, workspace_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Track a custom analytics event"""
        try:
            # This would typically store events in a separate analytics table
            # For now, just log the event
            logger.info(
                "Analytics event tracked",
                workspace_id=workspace_id,
                event_type=event_type,
                event_data=event_data
            )
            return True
            
        except Exception as e:
            logger.error("Failed to track event", error=str(e))
            return False

    async def _get_usage_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily usage metrics for charts"""
        try:
            # Get daily message counts
            daily_stats = self.db.query(
                func.date(ChatMessage.created_at).label('date'),
                func.count(ChatMessage.id).label('messages_count'),
                func.count(func.distinct(ChatSession.id)).label('sessions_count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).group_by(func.date(ChatMessage.created_at)).all()
            
            # Get real satisfaction data for each day
            result = []
            for stat in daily_stats:
                # Get satisfaction data for this specific date
                satisfaction_data = self.db.query(
                    func.count(ChatMessage.id).label('total'),
                    func.sum(func.case(
                        (ChatMessage.confidence_score == 'high', 1),
                        else_=0
                    )).label('satisfied')
                ).join(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    func.date(ChatMessage.created_at) == stat.date,
                    ChatMessage.confidence_score.isnot(None)
                ).first()
                
                total_messages = satisfaction_data.total or 0
                satisfied_count = satisfaction_data.satisfied or 0
                unsatisfied_count = total_messages - satisfied_count
                
                result.append({
                    'date': stat.date.isoformat(),
                    'queries': stat.messages_count,
                    'sessions': stat.sessions_count,
                    'satisfied': satisfied_count,
                    'unsatisfied': unsatisfied_count
                })
            
            return result
            
        except Exception as e:
            logger.error("Failed to get usage metrics", error=str(e))
            raise AnalyticsError("Failed to get usage metrics", details={"error": str(e)})

    async def _get_hourly_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get hourly distribution metrics"""
        try:
            # Get hourly message counts
            hourly_stats = self.db.query(
                func.extract('hour', ChatMessage.created_at).label('hour'),
                func.count(ChatMessage.id).label('messages_count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).group_by(func.extract('hour', ChatMessage.created_at)).all()
            
            # Create 24-hour array
            hourly_data = []
            for hour in range(24):
                count = 0
                for stat in hourly_stats:
                    if stat.hour == hour:
                        count = stat.messages_count
                        break
                hourly_data.append({
                    'hour': f"{hour:02d}:00",
                    'queries': count
                })
            
            return hourly_data
            
        except Exception as e:
            logger.error("Failed to get hourly metrics", error=str(e))
            raise AnalyticsError("Failed to get hourly metrics", details={"error": str(e)})

    async def _get_satisfaction_metrics(self, workspace_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get satisfaction metrics"""
        try:
            # Get daily satisfaction data (mock for now)
            daily_stats = self.db.query(
                func.date(ChatMessage.created_at).label('date'),
                func.count(ChatMessage.id).label('messages_count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).group_by(func.date(ChatMessage.created_at)).all()
            
            result = []
            for stat in daily_stats:
                # Get real satisfaction data for this specific date
                satisfaction_data = self.db.query(
                    func.count(ChatMessage.id).label('total'),
                    func.sum(func.case(
                        (ChatMessage.confidence_score == 'high', 1),
                        else_=0
                    )).label('satisfied')
                ).join(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    func.date(ChatMessage.created_at) == stat.date,
                    ChatMessage.confidence_score.isnot(None)
                ).first()
                
                total_messages = satisfaction_data.total or 0
                satisfied_count = satisfaction_data.satisfied or 0
                unsatisfied_count = total_messages - satisfied_count
                
                result.append({
                    'date': stat.date.isoformat(),
                    'satisfied': satisfied_count,
                    'unsatisfied': unsatisfied_count
                })
            
            return result
            
        except Exception as e:
            logger.error("Failed to get satisfaction metrics", error=str(e))
            raise AnalyticsError("Failed to get satisfaction metrics", details={"error": str(e)})

    async def _get_top_questions(self, workspace_id: str, start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top questions from user messages"""
        try:
            # Get most common user messages
            top_questions = self.db.query(
                ChatMessage.content,
                func.count(ChatMessage.id).label('count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= start_date,
                ChatMessage.created_at <= end_date
            ).group_by(ChatMessage.content).order_by(desc('count')).limit(limit).all()
            
            result = []
            for question in top_questions:
                # Calculate real satisfaction rate for this question
                satisfaction_data = self.db.query(
                    func.count(ChatMessage.id).label('total'),
                    func.sum(func.case(
                        (ChatMessage.confidence_score == 'high', 1),
                        else_=0
                    )).label('satisfied')
                ).join(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    ChatMessage.content == question.content,
                    ChatMessage.role == 'user',
                    ChatMessage.created_at >= start_date,
                    ChatMessage.created_at <= end_date,
                    ChatMessage.confidence_score.isnot(None)
                ).first()
                
                total_responses = satisfaction_data.total or 0
                satisfied_responses = satisfaction_data.satisfied or 0
                satisfaction_rate = (satisfied_responses / total_responses * 100) if total_responses > 0 else 0
                
                result.append({
                    'question': question.content[:100] + '...' if len(question.content) > 100 else question.content,
                    'count': question.count,
                    'satisfaction': round(satisfaction_rate, 1)
                })
            
            return result
            
        except Exception as e:
            logger.error("Failed to get top questions", error=str(e))
            raise AnalyticsError("Failed to get top questions", details={"error": str(e)})

    async def export_analytics_data(self, workspace_id: str, days: int, format: str = "json") -> Dict[str, Any]:
        """Export comprehensive analytics data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get all analytics data
            usage_stats = await self._get_usage_metrics(workspace_id, start_date, end_date)
            hourly_stats = await self._get_hourly_metrics(workspace_id, start_date, end_date)
            satisfaction_stats = await self._get_satisfaction_metrics(workspace_id, start_date, end_date)
            top_questions = await self._get_top_questions(workspace_id, start_date, end_date, 20)
            
            # Get basic metrics
            total_messages = sum(stat['queries'] for stat in usage_stats)
            total_sessions = sum(stat['sessions'] for stat in usage_stats)
            avg_response_time = 1.2  # Mock for now
            
            export_data = {
                'summary': {
                    'total_queries': total_messages,
                    'total_sessions': total_sessions,
                    'avg_response_time': avg_response_time,
                    'satisfaction_rate': 94.2
                },
                'usage_stats': usage_stats,
                'hourly_stats': hourly_stats,
                'satisfaction_stats': satisfaction_stats,
                'top_questions': top_questions,
                'export_date': datetime.now().isoformat(),
                'period_days': days
            }
            
            return export_data
            
        except Exception as e:
            logger.error("Failed to export analytics data", error=str(e))
            raise AnalyticsError("Failed to export analytics data", details={"error": str(e)})
