"""
API v1 router configuration
"""

from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, documents, chat, embed, analytics, vector_search, rag_query, chat_sessions, analytics_enhanced, analytics_dashboard, analytics_comprehensive, ab_testing, billing, billing_enhanced, workspace, white_label, health, embed_enhanced, performance, pricing, settings, widget_status, support, worker_health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(chat_sessions.router, prefix="/chat", tags=["chat-sessions"])
api_router.include_router(embed.router, prefix="/embed", tags=["embed"])
# Include enhanced embed routes (chat via API key, preview, code management)
api_router.include_router(embed_enhanced.router, prefix="/embed", tags=["embed"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(analytics_enhanced.router, prefix="/analytics", tags=["analytics-enhanced"])
api_router.include_router(analytics_dashboard.router, prefix="/analytics", tags=["analytics-dashboard"])
api_router.include_router(analytics_comprehensive.router, prefix="/analytics", tags=["analytics-comprehensive"])
api_router.include_router(ab_testing.router, prefix="/ab-testing", tags=["ab-testing"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(billing_enhanced.router, prefix="/billing", tags=["billing-enhanced"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
api_router.include_router(white_label.router, prefix="/white-label", tags=["white-label"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(widget_status.router, prefix="/widget", tags=["widget-status"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(worker_health.router, prefix="/workers", tags=["worker-health"])
api_router.include_router(vector_search.router, prefix="/vector", tags=["vector-search"])
api_router.include_router(rag_query.router, prefix="/rag", tags=["rag-query"])
