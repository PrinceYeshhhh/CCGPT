"""
Redis Queue setup for background jobs
"""

import redis
from rq import Queue
from app.core.config import settings

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)

# Create queues
ingest_queue = Queue(settings.RQ_QUEUE_NAME, connection=redis_conn)

def get_ingest_queue() -> Queue:
    """Get the ingest queue"""
    return ingest_queue
