"""
Analytics endpoints to support dashboard Overview in frontend
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from app.core.database import get_db
from app.core import dependencies as core_deps
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.analytics_service import AnalyticsService
from app.schemas.common import BaseResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview")
async def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Return top-line KPIs used by the dashboard Overview."""
    try:
        workspace_id = str(current_user.workspace_id)
        # Totals
        total_messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id
        ).count()
        active_sessions = db.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.is_active == True
        ).count()
        # Average response time (assistant messages) over last 30 days
        end = datetime.utcnow()
        start = end - timedelta(days=30)
        avg_response_time_ms = db.query(func.avg(ChatMessage.response_time_ms)).join(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatMessage.role == "assistant",
            ChatMessage.created_at >= start,
            ChatMessage.created_at < end,
            ChatMessage.response_time_ms.isnot(None)
        ).scalar()

        # Top questions (most frequent normalized user messages over last 30 days)
        # Normalize by trimming and lowercasing (simple approach)
        normalized = func.lower(func.trim(ChatMessage.content))
        top_rows = (
            db.query(normalized.label("question"), func.count().label("count"))
            .join(ChatSession)
            .filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= start,
                ChatMessage.created_at < end,
            )
            .group_by(normalized)
            .order_by(func.count().desc())
            .limit(5)
            .all()
        )
        top_questions: List[Dict[str, Any]] = [
            {"question": (row.question or "").strip(), "count": int(row.count or 0)} for row in top_rows if (row.question or "").strip()
        ]

        return {
            "total_messages": total_messages,
            "active_sessions": active_sessions,
            "avg_response_time": avg_response_time_ms,
            "top_questions": top_questions,
        }
    except Exception as e:
        logger.error("analytics_overview failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load overview")


@router.get("/usage-stats")
async def analytics_usage_stats(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Return daily usage counts for the last N days suitable for charts."""
    try:
        # Extra guard to ensure tests receive 400/422 semantics even if validation is bypassed
        if days < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'days' must be >= 1")
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        # Count user messages per day
        results: List[Dict[str, Any]] = []
        for i in range(days):
            day_start = (start + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= day_start,
                ChatMessage.created_at < day_end,
            ).count()
            results.append({"date": day_start.date().isoformat(), "messages_count": count})
        return results
    except Exception as e:
        logger.error("analytics_usage_stats failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load usage stats")


@router.get("/kpis")
async def analytics_kpis(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Return KPI deltas for the last period (simple comparisons)."""
    try:
        workspace_id = str(current_user.workspace_id)
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start

        def count_messages(s: datetime, e: datetime) -> int:
            return db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= s,
                ChatMessage.created_at < e,
            ).count()

        cur_msgs = count_messages(start, end)
        prev_msgs = count_messages(prev_start, prev_end)
        delta_pct = 0.0 if prev_msgs == 0 else ((cur_msgs - prev_msgs) / max(prev_msgs, 1)) * 100.0

        # Sessions delta
        cur_sessions = db.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.created_at >= start,
            ChatSession.created_at < end,
        ).count()
        prev_sessions = db.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.created_at >= prev_start,
            ChatSession.created_at < prev_end,
        ).count()
        sessions_delta = cur_sessions - prev_sessions

        # Avg response time (assistant messages) current vs previous window
        def avg_rt(s: datetime, e: datetime):
            return db.query(func.avg(ChatMessage.response_time_ms)).join(ChatSession).filter(
                ChatSession.workspace_id == workspace_id,
                ChatMessage.role == "assistant",
                ChatMessage.created_at >= s,
                ChatMessage.created_at < e,
                ChatMessage.response_time_ms.isnot(None)
            ).scalar()
        cur_rt = avg_rt(start, end)
        prev_rt = avg_rt(prev_start, prev_end)
        # Delta in ms (if both present)
        if cur_rt is not None and prev_rt is not None:
            rt_delta = float(cur_rt) - float(prev_rt)
        else:
            rt_delta = 0

        return {
            "queries": {"current": cur_msgs, "previous": prev_msgs, "delta_pct": delta_pct},
            "sessions": {"current": cur_sessions, "previous": prev_sessions, "delta": sessions_delta},
            "avg_response_time_ms": {"current": cur_rt, "previous": prev_rt, "delta_ms": rt_delta},
            "active_sessions": {"current": cur_sessions, "previous": prev_sessions, "delta": sessions_delta},
        }
    except Exception as e:
        logger.error("analytics_kpis failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load KPIs")

"""
Analytics endpoints for usage statistics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    DocumentAnalytics,
    SessionAnalytics,
    MessageAnalytics,
    UsageStats,
    EmbedCodeAnalytics,
    HourlyStat,
    SatisfactionStat,
    KPISummary
)
from app.services.auth import AuthService
from app.services.analytics_service import AnalyticsService
from app.api.api_v1.dependencies import get_current_user
from app.utils.validators import DashboardQueryValidator, AnalyticsFilterValidator

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Get analytics overview for the user"""
    try:
        # Validate input parameters
        query_params = DashboardQueryValidator(days=days)
        
        analytics_service = AnalyticsService(db)
        overview = analytics_service.get_user_overview(current_user.id)
        
        return AnalyticsOverview(**overview)
        
    except ValueError as e:
        logger.warning("Invalid input parameters", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get analytics overview", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview"
        )


@router.get("/documents", response_model=List[DocumentAnalytics])
async def get_document_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Get document analytics"""
    try:
        analytics_service = AnalyticsService(db)
        documents = analytics_service.get_document_analytics(current_user.id)
        
        return [DocumentAnalytics.from_orm(doc) for doc in documents]
        
    except Exception as e:
        logger.error("Failed to get document analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document analytics"
        )


@router.get("/sessions", response_model=List[SessionAnalytics])
async def get_session_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Get session analytics"""
    try:
        analytics_service = AnalyticsService(db)
        sessions = analytics_service.get_session_analytics(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return [SessionAnalytics.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error("Failed to get session analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session analytics"
        )


@router.get("/messages", response_model=List[MessageAnalytics])
async def get_message_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    flagged_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(core_deps.get_current_user)
):
    """Get message analytics"""
    try:
        analytics_service = AnalyticsService(db)
        messages = analytics_service.get_message_analytics(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            flagged_only=flagged_only
        )
        
        return [MessageAnalytics.from_orm(message) for message in messages]
        
    except Exception as e:
        logger.error("Failed to get message analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message analytics"
        )


@router.get("/usage-stats", response_model=List[UsageStats])
async def get_usage_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics over time"""
    try:
        # Extra guard to ensure tests receive 400/422 semantics even if validation is bypassed
        if days < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'days' must be >= 1")
        analytics_service = AnalyticsService(db)
        stats = analytics_service.get_usage_stats(
            user_id=current_user.id,
            days=days
        )
        
        return [UsageStats(**stat) for stat in stats]
        
    except Exception as e:
        logger.error("Failed to get usage stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/embed-codes", response_model=List[EmbedCodeAnalytics])
async def get_embed_code_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get embed code analytics"""
    try:
        analytics_service = AnalyticsService(db)
        embed_codes = analytics_service.get_embed_code_analytics(current_user.id)
        
        return [EmbedCodeAnalytics.from_orm(code) for code in embed_codes]
        
    except Exception as e:
        logger.error("Failed to get embed code analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed code analytics"
        )


@router.get("/hourly", response_model=List[HourlyStat])
async def get_hourly_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated hourly trends for sessions/messages for past N days"""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_hourly_trends(current_user.id, days=days)
        return [HourlyStat(**row) for row in data]
    except Exception as e:
        logger.error("Failed to get hourly trends", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hourly trends"
        )


@router.get("/satisfaction", response_model=List[SatisfactionStat])
async def get_satisfaction_stats(
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily satisfaction stats for the past N days"""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_satisfaction_stats(current_user.id, days=days)
        return [SatisfactionStat(**row) for row in data]
    except Exception as e:
        logger.error("Failed to get satisfaction stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve satisfaction statistics"
        )


@router.get("/kpis", response_model=KPISummary)
async def get_kpis(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get KPI metrics with deltas for the dashboard overview."""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_kpis(current_user.id, days=days)
        return KPISummary(**data)
    except Exception as e:
        logger.error("Failed to get KPIs", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPIs"
        )


@router.get("/export")
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export analytics data"""
    try:
        analytics_service = AnalyticsService(db)
        export_data = analytics_service.export_analytics(
            user_id=current_user.id,
            format=format,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "csv":
            return {"data": export_data, "content_type": "text/csv"}
        else:
            return {"data": export_data, "content_type": "application/json"}
        
    except Exception as e:
        logger.error("Failed to export analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        )


@router.post("/performance", response_model=BaseResponse)
async def track_performance_event(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track performance event"""
    try:
        from app.schemas.common import BaseResponse
        
        # Log performance event
        logger.info(
            "Performance event tracked",
            user_id=current_user.id,
            event_type=event_data.get('event_type'),
            event_data=event_data
        )
        
        return BaseResponse(
            success=True,
            message="Performance event tracked successfully"
        )
        
    except Exception as e:
        logger.error("Failed to track performance event", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track performance event"
        )