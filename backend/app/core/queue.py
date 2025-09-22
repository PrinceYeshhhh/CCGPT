"""
Enhanced Redis Queue setup for background jobs with priority support
"""

import redis
from rq import Queue, Worker, Connection
from rq.job import Job
from typing import Optional, Dict, Any
import structlog
from app.core.config import settings
from app.core.database import redis_manager

logger = structlog.get_logger()

# Redis connection with enhanced configuration
redis_conn = redis_manager.get_client()

# Create priority queues
high_priority_queue = Queue(settings.HIGH_PRIORITY_QUEUE, connection=redis_conn)
normal_queue = Queue(settings.NORMAL_QUEUE, connection=redis_conn)
low_priority_queue = Queue(settings.LOW_PRIORITY_QUEUE, connection=redis_conn)

# Legacy queue for backward compatibility
ingest_queue = normal_queue

class QueueManager:
    """Enhanced queue manager with priority support"""
    
    def __init__(self):
        self.queues = {
            'high': high_priority_queue,
            'normal': normal_queue,
            'low': low_priority_queue
        }
        self.workers = {}
    
    def get_queue(self, priority: str = 'normal') -> Queue:
        """Get queue by priority"""
        return self.queues.get(priority, normal_queue)
    
    def enqueue_job(
        self, 
        func, 
        *args, 
        priority: str = 'normal',
        timeout: int = 300,
        **kwargs
    ) -> Job:
        """Enqueue job with priority"""
        queue = self.get_queue(priority)
        
        job = queue.enqueue(
            func,
            *args,
            timeout=timeout,
            **kwargs
        )
        
        logger.info(
            f"Job enqueued",
            job_id=job.id,
            priority=priority,
            queue=queue.name
        )
        
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        for queue in self.queues.values():
            job = queue.fetch_job(job_id)
            if job:
                return job
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues"""
        stats = {}
        for priority, queue in self.queues.items():
            stats[priority] = {
                'name': queue.name,
                'length': len(queue),
                'failed_jobs': len(queue.failed_job_registry),
                'scheduled_jobs': len(queue.scheduled_job_registry)
            }
        return stats
    
    def start_worker(self, queue_names: list = None, **worker_kwargs):
        """Start worker for specified queues"""
        if queue_names is None:
            queue_names = ['normal']
        
        queues = [self.queues[name] for name in queue_names if name in self.queues]
        
        worker = Worker(queues, connection=redis_conn, **worker_kwargs)
        worker.work()
        
        return worker
    
    def cleanup_failed_jobs(self, older_than_hours: int = 24):
        """Clean up failed jobs older than specified hours"""
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        cleaned_count = 0
        for queue in self.queues.values():
            failed_jobs = queue.failed_job_registry.get_job_ids()
            for job_id in failed_jobs:
                job = queue.fetch_job(job_id)
                if job and job.failed_at and job.failed_at < cutoff_time:
                    queue.failed_job_registry.remove(job_id)
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} failed jobs")
        return cleaned_count

# Global queue manager
queue_manager = QueueManager()

def get_ingest_queue() -> Queue:
    """Get the ingest queue (backward compatibility)"""
    return queue_manager.get_queue('normal')

def get_high_priority_queue() -> Queue:
    """Get high priority queue"""
    return queue_manager.get_queue('high')

def get_normal_queue() -> Queue:
    """Get normal priority queue"""
    return queue_manager.get_queue('normal')

def get_low_priority_queue() -> Queue:
    """Get low priority queue"""
    return queue_manager.get_queue('low')

def enqueue_document_processing(document_id: str, priority: str = 'normal') -> Job:
    """Enqueue document processing job"""
    from app.worker.ingest_worker import process_document
    return queue_manager.enqueue_job(
        process_document,
        document_id,
        priority=priority,
        timeout=600  # 10 minutes
    )

def enqueue_embedding_processing(document_id: str, chunk_ids: list, priority: str = 'low') -> Job:
    """Enqueue embedding processing job"""
    from app.worker.ingest_worker import enqueue_embedding_jobs
    return queue_manager.enqueue_job(
        enqueue_embedding_jobs,
        document_id,
        chunk_ids,
        priority=priority,
        timeout=1800  # 30 minutes
    )
