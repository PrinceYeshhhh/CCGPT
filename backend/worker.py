#!/usr/bin/env python3
"""
RQ Worker script for document processing
"""

import os
import sys
import redis
from rq import Worker, Connection

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings

def main():
    """Start the RQ worker"""
    redis_conn = redis.from_url(settings.REDIS_URL)
    
    with Connection(redis_conn):
        worker = Worker([settings.RQ_QUEUE_NAME])
        print(f"Starting worker for queue: {settings.RQ_QUEUE_NAME}")
        worker.work()

if __name__ == "__main__":
    main()
