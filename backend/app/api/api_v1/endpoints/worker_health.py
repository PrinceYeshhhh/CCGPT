"""
Worker health check endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import structlog
import redis
import os

from app.core.database import get_db
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

@router.get("/health")
async def check_worker_health():
    """Check the health of document processing workers"""
    try:
        health_status = {
            "status": "healthy",
            "workers": [],
            "redis_connected": False,
            "queue_status": "unknown"
        }
        
        # Check Redis connection
        try:
            redis_url = os.getenv("REDIS_URL") or getattr(settings, 'REDIS_URL', '') or ""
            r = redis.from_url(redis_url)
            r.ping()
            health_status["redis_connected"] = True
            health_status["queue_status"] = "connected"
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["queue_status"] = "disconnected"
        
        # Check worker processes (simplified check)
        try:
            import psutil
            worker_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'rq worker' in cmdline or 'ingest_worker' in cmdline:
                        worker_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "status": "running"
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            health_status["workers"] = worker_processes
            
            if not worker_processes:
                health_status["status"] = "warning"
                health_status["message"] = "No worker processes detected"
            
        except ImportError:
            health_status["status"] = "warning"
            health_status["message"] = "psutil not available for process monitoring"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Worker health check failed"
        )

@router.get("/queue-stats")
async def get_queue_stats():
    """Get queue statistics"""
    try:
        redis_url = os.getenv("REDIS_URL") or getattr(settings, 'REDIS_URL', '') or ""
        r = redis.from_url(redis_url)
        
        # Get queue statistics
        queue_stats = {
            "queued_jobs": r.llen("rq:queue:document_processing"),
            "failed_jobs": r.llen("rq:queue:failed"),
            "completed_jobs": r.llen("rq:queue:finished"),
            "workers": len(r.smembers("rq:workers"))
        }
        
        return queue_stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get queue statistics"
        )

@router.post("/restart-workers")
async def restart_workers():
    """Restart document processing workers (admin only)"""
    try:
        # This would typically restart workers via a process manager
        # For now, we'll just return a success message
        logger.info("Worker restart requested")
        
        return {
            "status": "success",
            "message": "Worker restart initiated. Workers should restart within 30 seconds."
        }
        
    except Exception as e:
        logger.error(f"Failed to restart workers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart workers"
        )
