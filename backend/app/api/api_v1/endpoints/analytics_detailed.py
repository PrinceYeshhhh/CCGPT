"""
Detailed Analytics endpoints to support frontend Analytics page
Provides comprehensive analytics data with detailed breakdowns
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/detailed-overview")
async def detailed_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return detailed analytics overview with comprehensive metrics."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Total messages
        total_messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.created_at >= start
        ).count()
        
        # Active sessions
        active_sessions = db.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.is_active == True
        ).count()
        
        # Average response time
        avg_response_time = db.query(func.avg(ChatMessage.response_time_ms)).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.role == "assistant",
            ChatMessage.created_at >= start,
            ChatMessage.response_time_ms.isnot(None)
        ).scalar() or 0
        
        # User satisfaction (mock data for now)
        satisfaction_score = 4.2
        
        # Documents processed
        documents_processed = db.query(Document).filter(
            Document.workspace_id == workspace_id,
            Document.created_at >= start,
            Document.status == 'processed'
        ).count()
        
        # Top questions
        top_questions = db.query(
            func.lower(func.trim(ChatMessage.content)).label("question"),
            func.count().label("count")
        ).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= start
        ).group_by(func.lower(func.trim(ChatMessage.content))).order_by(
            func.count().desc()
        ).limit(5).all()
        
        top_questions_list = [
            {"question": row.question.strip(), "count": row.count}
            for row in top_questions if row.question.strip()
        ]
        
        from app.schemas.common import BaseResponse
        
        return BaseResponse(
            success=True,
            message="Analytics overview retrieved successfully",
            data={
                "total_messages": total_messages,
                "active_sessions": active_sessions,
                "avg_response_time": float(avg_response_time),
                "satisfaction_score": satisfaction_score,
                "documents_processed": documents_processed,
                "top_questions": top_questions_list,
                "period_days": days
            }
        ).dict()
        
    except Exception as e:
        logger.error("detailed_overview failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to load detailed overview"
        )


@router.get("/detailed-usage-stats")
async def detailed_usage_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return detailed usage statistics for charts."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Daily usage data
        daily_data = []
        for i in range(days):
            day_start = (start + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Messages per day
            messages_count = db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.created_at >= day_start,
                ChatMessage.created_at < day_end
            ).count()
            
            # Sessions per day
            sessions_count = db.query(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatSession.created_at >= day_start,
                ChatSession.created_at < day_end
            ).count()
            
            # Documents uploaded per day
            documents_count = db.query(Document).filter(
                Document.workspace_id == workspace_id,
                Document.created_at >= day_start,
                Document.created_at < day_end
            ).count()
            
            daily_data.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "messages": messages_count,
                "sessions": sessions_count,
                "documents": documents_count
            })
        
        from app.schemas.common import BaseResponse
        
        return BaseResponse(
            success=True,
            message="Usage statistics retrieved successfully",
            data=daily_data
        ).dict()
        
    except Exception as e:
        logger.error("detailed_usage_stats failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load usage statistics"
        )


@router.get("/detailed-hourly")
async def detailed_hourly(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return hourly usage patterns for the last N days."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Hourly data for the last N days
        hourly_data = []
        for i in range(days):
            day_start = (start + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            for hour in range(24):
                hour_start = day_start + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                messages_count = db.query(ChatMessage).join(ChatSession).filter(
                    ChatSession.workspace_id == workspace_id,
                    ChatMessage.created_at >= hour_start,
                    ChatMessage.created_at < hour_end
                ).count()
                
                hourly_data.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "hour": hour,
                    "messages": messages_count
                })
        
        from app.schemas.common import BaseResponse
        
        return BaseResponse(
            success=True,
            message="Hourly data retrieved successfully",
            data=hourly_data
        ).dict()
        
    except Exception as e:
        logger.error("detailed_hourly failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load hourly data"
        )


@router.get("/detailed-satisfaction")
async def detailed_satisfaction(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return satisfaction metrics and trends."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Mock satisfaction data (would come from feedback system)
        satisfaction_data = []
        for i in range(days):
            day_start = (start + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Simulate satisfaction scores (4.0-5.0 range)
            import random
            base_score = 4.2
            variation = random.uniform(-0.3, 0.3)
            score = max(1.0, min(5.0, base_score + variation))
            
            satisfaction_data.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "score": round(score, 1),
                "responses": random.randint(5, 25)
            })
        
        # Overall metrics
        avg_score = sum(d["score"] for d in satisfaction_data) / len(satisfaction_data)
        total_responses = sum(d["responses"] for d in satisfaction_data)
        
        from app.schemas.common import BaseResponse
        
        return BaseResponse(
            success=True,
            message="Satisfaction data retrieved successfully",
            data={
                "daily_scores": satisfaction_data,
                "average_score": round(avg_score, 1),
                "total_responses": total_responses,
                "trend": "stable"  # Would calculate actual trend
            }
        ).dict()
        
    except Exception as e:
        logger.error("detailed_satisfaction failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load satisfaction data"
        )


@router.get("/detailed-top-questions")
async def detailed_top_questions(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return top questions with detailed metrics."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Get top questions with counts
        top_questions = db.query(
            func.lower(func.trim(ChatMessage.content)).label("question"),
            func.count().label("count"),
            func.avg(ChatMessage.response_time_ms).label("avg_response_time")
        ).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= start
        ).group_by(func.lower(func.trim(ChatMessage.content))).order_by(
            func.count().desc()
        ).limit(limit).all()
        
        questions_list = []
        for row in top_questions:
            if row.question.strip():
                questions_list.append({
                    "question": row.question.strip(),
                    "count": row.count,
                    "avg_response_time": float(row.avg_response_time or 0),
                    "frequency_percent": 0  # Would calculate percentage
                })
        
        from app.schemas.common import BaseResponse
        
        return BaseResponse(
            success=True,
            message="Top questions retrieved successfully",
            data=questions_list
        ).dict()
        
    except Exception as e:
        logger.error("detailed_top_questions failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load top questions"
        )


@router.get("/detailed-export")
async def detailed_export(
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export detailed analytics data in various formats."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Get comprehensive data
        messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.created_at >= start
        ).all()
        
        sessions = db.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.created_at >= start
        ).all()
        
        documents = db.query(Document).filter(
            Document.workspace_id == workspace_id,
            Document.created_at >= start
        ).all()
        
        # Prepare export data
        export_data = {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": days
            },
            "summary": {
                "total_messages": len(messages),
                "total_sessions": len(sessions),
                "total_documents": len(documents)
            },
            "messages": [
                {
                    "id": str(msg.id),
                    "content": msg.content,
                    "role": msg.role,
                    "created_at": msg.created_at.isoformat(),
                    "response_time_ms": msg.response_time_ms
                }
                for msg in messages
            ],
            "sessions": [
                {
                    "id": str(session.id),
                    "created_at": session.created_at.isoformat(),
                    "is_active": session.is_active,
                    "message_count": len(session.messages)
                }
                for session in sessions
            ],
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat(),
                    "file_size": doc.file_size
                }
                for doc in documents
            ]
        }
        
        from app.schemas.common import BaseResponse
        
        if format == "json":
            return BaseResponse(
                success=True,
                message="Data exported successfully",
                data=export_data
            ).dict()
        elif format == "csv":
            # Would implement CSV conversion
            return BaseResponse(
                success=False,
                message="CSV export not yet implemented",
                data=None
            ).dict()
        elif format == "xlsx":
            # Would implement Excel conversion
            return BaseResponse(
                success=False,
                message="Excel export not yet implemented",
                data=None
            ).dict()
        
    except Exception as e:
        logger.error("detailed_export failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )
