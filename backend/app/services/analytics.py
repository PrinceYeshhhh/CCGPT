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

logger = structlog.get_logger()


class AnalyticsService:
    """Analytics service for generating insights and statistics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_overview(self, user_id: int) -> Dict[str, Any]:
        """Get analytics overview for a user"""
        try:
            # Document statistics
            total_documents = self.db.query(Document).filter(
                Document.uploaded_by == user_id
            ).count()
            
            total_chunks = self.db.query(DocumentChunk).join(Document).filter(
                Document.uploaded_by == user_id
            ).count()
            
            # Session statistics
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).count()
            
            active_sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).count()
            
            # Message statistics
            total_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.user_id == user_id
            ).count()
            
            # Response time statistics
            response_times = self.db.query(ChatMessage.response_time_ms).join(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatMessage.response_time_ms.isnot(None)
            ).all()
            
            avg_response_time = 0
            if response_times:
                avg_response_time = sum(rt[0] for rt in response_times) / len(response_times)
            
            # Confidence statistics
            confidence_scores = self.db.query(ChatMessage.confidence_score).join(ChatSession).filter(
                ChatSession.user_id == user_id,
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
            
            # Top questions (most frequent user messages)
            top_questions = self.db.query(
                ChatMessage.content,
                func.count(ChatMessage.id).label('count')
            ).join(ChatSession).filter(
                ChatSession.user_id == user_id,
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
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get daily statistics
            daily_stats = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Sessions count
                sessions_count = self.db.query(ChatSession).filter(
                    ChatSession.user_id == user_id,
                    ChatSession.created_at >= current_date,
                    ChatSession.created_at < next_date
                ).count()
                
                # Messages count
                messages_count = self.db.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.user_id == user_id,
                    ChatMessage.created_at >= current_date,
                    ChatMessage.created_at < next_date
                ).count()
                
                # Documents uploaded
                documents_uploaded = self.db.query(Document).filter(
                    Document.uploaded_by == user_id,
                    Document.uploaded_at >= current_date,
                    Document.uploaded_at < next_date
                ).count()
                
                # Average session duration
                sessions = self.db.query(ChatSession).filter(
                    ChatSession.user_id == user_id,
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
