"""
Vector search endpoints for similarity search
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.vector_search import VectorSearchRequest, VectorSearchResponse
from app.services.auth import AuthService
from app.services.vector_service import VectorService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Perform vector similarity search"""
    try:
        vector_service = VectorService()
        
        # Use user_id as workspace_id for now
        workspace_id = str(current_user.id)
        
        # Perform vector search
        results = await vector_service.vector_search(
            workspace_id=workspace_id,
            query=request.query,
            top_k=request.top_k or 5
        )
        
        logger.info(
            "Vector search completed",
            user_id=current_user.id,
            query=request.query[:100],
            results_count=len(results)
        )
        
        return VectorSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(
            "Vector search failed",
            error=str(e),
            user_id=current_user.id,
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector search failed"
        )


@router.get("/search", response_model=VectorSearchResponse)
async def vector_search_get(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=50, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Perform vector similarity search via GET"""
    try:
        vector_service = VectorService()
        
        # Use user_id as workspace_id for now
        workspace_id = str(current_user.id)
        
        # Perform vector search
        results = await vector_service.vector_search(
            workspace_id=workspace_id,
            query=query,
            top_k=top_k
        )
        
        logger.info(
            "Vector search completed",
            user_id=current_user.id,
            query=query[:100],
            results_count=len(results)
        )
        
        return VectorSearchResponse(
            query=query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(
            "Vector search failed",
            error=str(e),
            user_id=current_user.id,
            query=query[:100]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector search failed"
        )


@router.delete("/cache")
async def clear_vector_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Clear vector search cache for current user"""
    try:
        from app.services.vector_search_service import vector_search_service
        
        # Use user_id as workspace_id for now
        workspace_id = str(current_user.id)
        
        # Clear cache
        success = await vector_search_service.clear_cache(workspace_id)
        
        if success:
            logger.info("Vector cache cleared", user_id=current_user.id)
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
        
    except Exception as e:
        logger.error("Cache clear failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get("/stats")
async def get_vector_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService(db).get_current_user)
):
    """Get vector search statistics"""
    try:
        vector_service = VectorService()
        from app.services.vector_search_service import vector_search_service
        
        # Get collection stats
        collection_stats = vector_service.get_collection_stats()
        
        # Get cache stats
        cache_stats = await vector_search_service.get_cache_stats()
        
        # Get embedding service stats
        from app.services.embeddings_service import embeddings_service
        embedding_stats = embeddings_service.get_embedding_stats()
        
        return {
            "collection": collection_stats,
            "cache": cache_stats,
            "embeddings": embedding_stats
        }
        
    except Exception as e:
        logger.error("Failed to get vector stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )
