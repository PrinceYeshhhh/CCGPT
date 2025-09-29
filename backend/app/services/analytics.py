"""
Analytics service for generating usage statistics and insights
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, date, timedelta
import structlog

from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.embed import EmbedCode
from app.models.user import User
from app.utils.cache import analytics_cache

logger = structlog.get_logger()


class AnalyticsService:
    """Analytics service for generating insights and statistics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_overview(self, user_id: int) -> Dict[str, Any]:
        """Get analytics overview for a user"""
        try:
            # Get user's workspace_id for proper isolation
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            workspace_id = user.workspace_id
            
            # Document statistics (by workspace)
            total_documents = self.db.query(Document).filter(
                Document.workspace_id == workspace_id
            ).count()
            
            total_chunks = self.db.query(DocumentChunk).join(Document).filter(
                Document.workspace_id == workspace_id
            ).count()
            
            # Session statistics (by workspace)
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id
            ).count()
            
            active_sessions = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.is_active == True
            ).count()
            
            # Message statistics (by workspace)
            total_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id
            ).count()
            
            # Response time statistics (by workspace)
            response_times = self.db.query(ChatMessage.response_time_ms).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.response_time_ms.isnot(None)
            ).all()
            
            avg_response_time = 0
            if response_times:
                avg_response_time = sum(rt[0] for rt in response_times) / len(response_times)
            
            # Confidence statistics (by workspace)
            confidence_scores = self.db.query(ChatMessage.confidence_score).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.confidence_score.isnot(None)
            ).all()
            
            avg_confidence = "medium"
            if confidence_scores:
                high_count = sum(1 for c in confidence_scores if c[0] == "high")
                medium_count = sum(1 for c in confidence_scores if c[0] == "medium")
                low_count = sum(1 for c in confidence_scores if c[0] == "low")
                
                total = high_count + medium_count + low_count
                if total > 0:
                    if high_count / total > 0.6:
                        avg_confidence = "high"
                    elif low_count / total > 0.6:
                        avg_confidence = "low"
            
            # Top questions (most frequent user messages by workspace)
            top_questions = self.db.query(
                ChatMessage.content,
                func.count(ChatMessage.id).label('count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'user'
            ).group_by(ChatMessage.content).order_by(
                desc('count')
            ).limit(5).all()
            
            top_questions_list = [
                {"question": q[0][:100] + "..." if len(q[0]) > 100 else q[0], "count": q[1]}
                for q in top_questions
            ]
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "active_sessions": active_sessions,
                "avg_response_time": round(avg_response_time, 2),
                "avg_confidence": avg_confidence,
                "top_questions": top_questions_list
            }
            
        except Exception as e:
            logger.error("Failed to get user overview", error=str(e), user_id=user_id)
            raise
    
    def get_document_analytics(self, user_id: int) -> List[Document]:
        """Get document analytics"""
        try:
            documents = self.db.query(Document).filter(
                Document.uploaded_by == user_id
            ).order_by(desc(Document.uploaded_at)).all()
            
            return documents
            
        except Exception as e:
            logger.error("Failed to get document analytics", error=str(e), user_id=user_id)
            raise
    
    def get_session_analytics(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ChatSession]:
        """Get session analytics"""
        try:
            query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
            
            if start_date:
                query = query.filter(ChatSession.created_at >= start_date)
            
            if end_date:
                query = query.filter(ChatSession.created_at <= end_date)
            
            sessions = query.order_by(desc(ChatSession.created_at)).offset(skip).limit(limit).all()
            
            return sessions
            
        except Exception as e:
            logger.error("Failed to get session analytics", error=str(e), user_id=user_id)
            raise
    
    def get_message_analytics(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        flagged_only: bool = False
    ) -> List[ChatMessage]:
        """Get message analytics"""
        try:
            query = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.user_id == user_id
            )
            
            if flagged_only:
                query = query.filter(ChatMessage.is_flagged == True)
            
            messages = query.order_by(desc(ChatMessage.created_at)).offset(skip).limit(limit).all()
            
            return messages
            
        except Exception as e:
            logger.error("Failed to get message analytics", error=str(e), user_id=user_id)
            raise
    
    def get_usage_stats(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage statistics over time"""
        try:
            # Get user's workspace_id for proper isolation
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            workspace_id = user.workspace_id
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get daily statistics
            daily_stats = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Sessions count (by workspace)
                sessions_count = self.db.query(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    ChatSession.created_at >= current_date,
                    ChatSession.created_at < next_date
                ).count()
                
                # Messages count (user queries only by workspace)
                messages_count = self.db.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    ChatMessage.role == 'user',
                    ChatMessage.created_at >= current_date,
                    ChatMessage.created_at < next_date
                ).count()
                
                # Documents uploaded (by workspace)
                documents_uploaded = self.db.query(Document).filter(
                    Document.workspace_id == workspace_id,
                    Document.uploaded_at >= current_date,
                    Document.uploaded_at < next_date
                ).count()
                
                # Average session duration (by workspace)
                sessions = self.db.query(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    ChatSession.created_at >= current_date,
                    ChatSession.created_at < next_date,
                    ChatSession.ended_at.isnot(None)
                ).all()
                
                avg_duration = 0
                if sessions:
                    durations = []
                    for session in sessions:
                        if session.ended_at:
                            duration = (session.ended_at - session.created_at).total_seconds() / 60
                            durations.append(duration)
                    
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                
                daily_stats.append({
                    "date": current_date,
                    "sessions_count": sessions_count,
                    "messages_count": messages_count,
                    "documents_uploaded": documents_uploaded,
                    "avg_session_duration": round(avg_duration, 2)
                })
                
                current_date = next_date
            
            return daily_stats
            
        except Exception as e:
            logger.error("Failed to get usage stats", error=str(e), user_id=user_id)
            raise
    
    def get_hourly_trends(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get aggregated hourly query/session counts for the past N days"""
        try:
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=days)
            period_key = f"{days}d"
            # Cache key uses user_id as workspace proxy for now
            cached = analytics_cache.get_hourly_trends_sync(str(user_id), period_key)
            if cached:
                return cached
            # Initialize 24-hour buckets
            buckets = {h: {"hour": h, "sessions_count": 0, "messages_count": 0} for h in range(24)}
            # Aggregate sessions by hour
            sessions = self.db.query(ChatSession.created_at).filter(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= start_dt,
                ChatSession.created_at < end_dt,
            ).all()
            for (created_at,) in sessions:
                h = created_at.hour
                buckets[h]["sessions_count"] += 1
            # Aggregate messages by hour (user + assistant)
            messages = self.db.query(ChatMessage.created_at).join(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatMessage.created_at >= start_dt,
                ChatMessage.created_at < end_dt,
            ).all()
            for (created_at,) in messages:
                h = created_at.hour
                buckets[h]["messages_count"] += 1
            result = [buckets[h] for h in range(24)]
            analytics_cache.set_hourly_trends_sync(str(user_id), period_key, result)
            return result
        except Exception as e:
            logger.error("Failed to get hourly trends", error=str(e), user_id=user_id)
            raise

    def get_satisfaction_stats(
        self,
        user_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Compute daily satisfied/unsatisfied counts.
        Uses confidence_score as a proxy if no explicit satisfaction flag exists.
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            period_key = f"{days}d"
            cached = analytics_cache.get_satisfaction_sync(str(user_id), period_key)
            if cached:
                return cached
            stats: List[Dict[str, Any]] = []
            current = start_date
            while current <= end_date:
                next_day = current + timedelta(days=1)
                # Heuristic: assistant messages with high/medium confidence are satisfied
                satisfied = self.db.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.user_id == user_id,
                    ChatMessage.role == 'assistant',
                    ChatMessage.created_at >= current,
                    ChatMessage.created_at < next_day,
                    ChatMessage.confidence_score.in_(['high', 'medium'])
                ).count()
                # Unsatisfied: assistant messages with low confidence or flagged
                unsatisfied = self.db.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.user_id == user_id,
                    ChatMessage.role == 'assistant',
                    ChatMessage.created_at >= current,
                    ChatMessage.created_at < next_day,
                ).filter(
                    (ChatMessage.confidence_score == 'low') | (ChatMessage.is_flagged == True)
                ).count()
                stats.append({
                    "date": current,
                    "satisfied": satisfied,
                    "unsatisfied": unsatisfied,
                })
                current = next_day
            analytics_cache.set_satisfaction_sync(str(user_id), period_key, stats)
            return stats
        except Exception as e:
            logger.error("Failed to get satisfaction stats", error=str(e), user_id=user_id)
            raise

    def get_kpis(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Compute KPI metrics and deltas for the dashboard overview.
        Metrics: queries (user messages), sessions, active sessions, avg response time, top questions (current window).
        Deltas compare current window vs previous window.
        """
        try:
            # Get user's workspace_id for proper isolation
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            workspace_id = user.workspace_id
            
            now_dt = datetime.utcnow()
            current_start = now_dt - timedelta(days=days)
            prev_start = current_start - timedelta(days=days)
            prev_end = current_start

            # Queries (user messages by workspace)
            msgs_current = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= current_start,
                ChatMessage.created_at < now_dt
            ).count()
            msgs_prev = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= prev_start,
                ChatMessage.created_at < prev_end
            ).count()

            # Sessions created (by workspace)
            sess_current = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= current_start,
                ChatSession.created_at < now_dt
            ).count()
            sess_prev = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= prev_start,
                ChatSession.created_at < prev_end
            ).count()

            # Active sessions (activity in window by workspace)
            active_current = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.last_activity_at >= current_start,
                ChatSession.last_activity_at < now_dt
            ).count()
            active_prev = self.db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.last_activity_at >= prev_start,
                ChatSession.last_activity_at < prev_end
            ).count()

            # Avg response time (assistant messages by workspace)
            rt_curr_rows = self.db.query(ChatMessage.response_time_ms).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'assistant',
                ChatMessage.response_time_ms.isnot(None),
                ChatMessage.created_at >= current_start,
                ChatMessage.created_at < now_dt
            ).all()
            rt_prev_rows = self.db.query(ChatMessage.response_time_ms).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'assistant',
                ChatMessage.response_time_ms.isnot(None),
                ChatMessage.created_at >= prev_start,
                ChatMessage.created_at < prev_end
            ).all()
            avg_rt_curr = round(sum(r[0] for r in rt_curr_rows) / len(rt_curr_rows), 2) if rt_curr_rows else 0
            avg_rt_prev = round(sum(r[0] for r in rt_prev_rows) / len(rt_prev_rows), 2) if rt_prev_rows else 0

            # Top questions in current window (by workspace)
            top_q = self.db.query(
                ChatMessage.content,
                func.count(ChatMessage.id).label('count')
            ).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= current_start,
                ChatMessage.created_at < now_dt
            ).group_by(ChatMessage.content).order_by(desc('count')).limit(5).all()
            top_questions_current = [
                {"question": t[0][:100] + "..." if len(t[0]) > 100 else t[0], "count": t[1]}
                for t in top_q
            ]

            def pct_change(curr: int, prev: int) -> float:
                if prev == 0:
                    return 100.0 if curr > 0 else 0.0
                return round(((curr - prev) / prev) * 100.0, 2)

            kpis = {
                "window_days": days,
                "queries": {"current": msgs_current, "previous": msgs_prev, "delta_pct": pct_change(msgs_current, msgs_prev)},
                "sessions": {"current": sess_current, "previous": sess_prev, "delta_pct": pct_change(sess_current, sess_prev)},
                "active_sessions": {"current": active_current, "previous": active_prev, "delta": active_current - active_prev},
                "avg_response_time_ms": {"current": avg_rt_curr, "previous": avg_rt_prev, "delta_ms": round(avg_rt_curr - avg_rt_prev, 2)},
                "top_questions_current": top_questions_current,
            }
            return kpis
        except Exception as e:
            logger.error("Failed to compute KPIs", error=str(e), user_id=user_id)
            raise
    
    def get_embed_code_analytics(self, user_id: int) -> List[EmbedCode]:
        """Get embed code analytics"""
        try:
            embed_codes = self.db.query(EmbedCode).filter(
                EmbedCode.user_id == user_id
            ).order_by(desc(EmbedCode.created_at)).all()
            
            return embed_codes
            
        except Exception as e:
            logger.error("Failed to get embed code analytics", error=str(e), user_id=user_id)
            raise
    
    def export_analytics(
        self,
        user_id: int,
        format: str = "json",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Any:
        """Export analytics data"""
        try:
            # Get all data for export
            documents = self.get_document_analytics(user_id)
            sessions = self.get_session_analytics(user_id, limit=1000, start_date=start_date, end_date=end_date)
            messages = self.get_message_analytics(user_id, limit=1000)
            embed_codes = self.get_embed_code_analytics(user_id)
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "user_id": user_id,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "status": doc.status,
                        "created_at": doc.created_at.isoformat(),
                        "chunks_count": len(doc.chunks)
                    }
                    for doc in documents
                ],
                "sessions": [
                    {
                        "id": session.id,
                        "session_id": session.session_id,
                        "created_at": session.created_at.isoformat(),
                        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                        "is_active": session.is_active,
                        "message_count": len(session.messages)
                    }
                    for session in sessions
                ],
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                        "response_time_ms": msg.response_time_ms,
                        "confidence_score": msg.confidence_score,
                        "is_flagged": msg.is_flagged,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in messages
                ],
                "embed_codes": [
                    {
                        "id": code.id,
                        "code_name": code.code_name,
                        "usage_count": code.usage_count,
                        "is_active": code.is_active,
                        "created_at": code.created_at.isoformat()
                    }
                    for code in embed_codes
                ]
            }
            
            if format == "csv":
                # Convert to CSV format (simplified)
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow(["Type", "ID", "Data"])
                
                # Write data
                for doc in documents:
                    writer.writerow(["Document", doc.id, f"{doc.filename} - {doc.status}"])
                
                for session in sessions:
                    writer.writerow(["Session", session.id, f"{session.session_id} - {len(session.messages)} messages"])
                
                for msg in messages:
                    writer.writerow(["Message", msg.id, f"{msg.role} - {msg.content[:50]}..."])
                
                return output.getvalue()
            
            return export_data
            
        except Exception as e:
            logger.error("Failed to export analytics", error=str(e), user_id=user_id)
            raise
