"""
Enhanced analytics endpoints for admin dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, extract
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.embed import EmbedCode
from app.services.auth import AuthService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get analytics summary for dashboard overview"""
    try:
        # Get workspace_id (assuming user.id as workspace for now)
        workspace_id = str(current_user.id)
        
        # Total documents
        total_documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).count()
        
        # Total chunks
        total_chunks = db.query(func.count()).select_from(Document).join(
            Document.chunks
        ).filter(Document.user_id == current_user.id).scalar() or 0
        
        # Total sessions
        total_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        # Total messages
        total_messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        # Active sessions (last 24 hours)
        active_sessions = db.query(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatSession.is_active == True,
                ChatSession.updated_at >= datetime.now() - timedelta(hours=24)
            )
        ).count()
        
        # Average response time
        avg_response_time = db.query(func.avg(ChatMessage.response_time_ms)).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.response_time_ms.isnot(None)
            )
        ).scalar() or 0
        
        # Average confidence
        confidence_scores = db.query(ChatMessage.confidence_score).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.confidence_score.isnot(None)
            )
        ).all()
        
        if confidence_scores:
            high_count = sum(1 for score in confidence_scores if score[0] == 'high')
            medium_count = sum(1 for score in confidence_scores if score[0] == 'medium')
            low_count = sum(1 for score in confidence_scores if score[0] == 'low')
            total = len(confidence_scores)
            
            if high_count / total >= 0.6:
                avg_confidence = 'high'
            elif medium_count / total >= 0.4:
                avg_confidence = 'medium'
            else:
                avg_confidence = 'low'
        else:
            avg_confidence = 'unknown'
        
        # Top questions (last 30 days)
        top_questions = db.query(
            ChatMessage.content,
            func.count(ChatMessage.id).label('count')
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= datetime.now() - timedelta(days=30)
            )
        ).group_by(ChatMessage.content).order_by(desc('count')).limit(5).all()
        
        top_questions_list = [
            {"question": question[0], "count": question[1]}
            for question in top_questions
        ]
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "active_sessions": active_sessions,
            "avg_response_time": int(avg_response_time) if avg_response_time else 0,
            "avg_confidence": avg_confidence,
            "top_questions": top_questions_list
        }
        
    except Exception as e:
        logger.error("Failed to get analytics summary", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.get("/queries-over-time")
async def get_queries_over_time(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get queries over time for charts"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Get daily message counts
        daily_messages = db.query(
            func.date(ChatMessage.created_at).label('date'),
            func.count(ChatMessage.id).label('messages_count')
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.created_at >= start_date
            )
        ).group_by(func.date(ChatMessage.created_at)).order_by('date').all()
        
        # Get daily session counts
        daily_sessions = db.query(
            func.date(ChatSession.created_at).label('date'),
            func.count(ChatSession.id).label('sessions_count')
        ).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatSession.created_at >= start_date
            )
        ).group_by(func.date(ChatSession.created_at)).order_by('date').all()
        
        # Combine data
        data_dict = {}
        for msg in daily_messages:
            date_str = msg[0].isoformat()
            data_dict[date_str] = {
                "date": date_str,
                "messages": msg[1],
                "sessions": 0
            }
        
        for session in daily_sessions:
            date_str = session[0].isoformat()
            if date_str in data_dict:
                data_dict[date_str]["sessions"] = session[1]
            else:
                data_dict[date_str] = {
                    "date": date_str,
                    "messages": 0,
                    "sessions": session[1]
                }
        
        return list(data_dict.values())
        
    except Exception as e:
        logger.error("Failed to get queries over time", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queries over time"
        )


@router.get("/top-queries")
async def get_top_queries(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get top queries for charts"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        top_queries = db.query(
            ChatMessage.content,
            func.count(ChatMessage.id).label('count')
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.role == 'user',
                ChatMessage.created_at >= start_date
            )
        ).group_by(ChatMessage.content).order_by(desc('count')).limit(limit).all()
        
        return [
            {"query": query[0], "count": query[1]}
            for query in top_queries
        ]
        
    except Exception as e:
        logger.error("Failed to get top queries", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top queries"
        )


@router.get("/file-usage")
async def get_file_usage(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get file usage statistics for charts"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Get document usage from sources_used in chat messages
        file_usage = db.query(
            Document.original_filename,
            func.count(ChatMessage.id).label('usage_count')
        ).join(
            Document.chunks
        ).join(
            ChatMessage.sources_used
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.created_at >= start_date,
                ChatMessage.sources_used.isnot(None)
            )
        ).group_by(Document.original_filename).order_by(desc('usage_count')).all()
        
        total_usage = sum(usage[1] for usage in file_usage)
        
        return [
            {
                "filename": usage[0],
                "usage_count": usage[1],
                "percentage": round((usage[1] / total_usage * 100), 2) if total_usage > 0 else 0
            }
            for usage in file_usage
        ]
        
    except Exception as e:
        logger.error("Failed to get file usage", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file usage"
        )


@router.get("/embed-codes")
async def get_embed_codes_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get embed codes analytics"""
    try:
        # Get embed codes for user
        embed_codes = db.query(EmbedCode).filter(
            EmbedCode.user_id == current_user.id
        ).all()
        
        total_embed_codes = len(embed_codes)
        active_embed_codes = sum(1 for code in embed_codes if code.is_active)
        total_usage = sum(code.usage_count for code in embed_codes)
        
        return {
            "total_embed_codes": total_embed_codes,
            "active_embed_codes": active_embed_codes,
            "total_usage": total_usage,
            "embed_codes": [
                {
                    "id": str(code.id),
                    "name": code.code_name,
                    "is_active": code.is_active,
                    "usage_count": code.usage_count,
                    "last_used": code.last_used.isoformat() if code.last_used else None,
                    "created_at": code.created_at.isoformat()
                }
                for code in embed_codes
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get embed codes analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed codes analytics"
        )


@router.get("/response-quality")
async def get_response_quality(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get response quality metrics"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Get confidence distribution
        confidence_dist = db.query(
            ChatMessage.confidence_score,
            func.count(ChatMessage.id).label('count')
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.role == 'assistant',
                ChatMessage.created_at >= start_date,
                ChatMessage.confidence_score.isnot(None)
            )
        ).group_by(ChatMessage.confidence_score).all()
        
        # Get average response time by confidence
        avg_response_time = db.query(
            ChatMessage.confidence_score,
            func.avg(ChatMessage.response_time_ms).label('avg_time')
        ).join(ChatSession).filter(
            and_(
                ChatSession.user_id == current_user.id,
                ChatMessage.role == 'assistant',
                ChatMessage.created_at >= start_date,
                ChatMessage.response_time_ms.isnot(None),
                ChatMessage.confidence_score.isnot(None)
            )
        ).group_by(ChatMessage.confidence_score).all()
        
        return {
            "confidence_distribution": [
                {"confidence": dist[0], "count": dist[1]}
                for dist in confidence_dist
            ],
            "avg_response_time_by_confidence": [
                {"confidence": time[0], "avg_time": float(time[1]) if time[1] else 0}
                for time in avg_response_time
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get response quality", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve response quality"
        )
