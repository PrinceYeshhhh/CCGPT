#!/bin/bash
set -e

# Production startup script for CustomerCareGPT Backend

echo "🚀 Starting CustomerCareGPT Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python -c "
import time
import psycopg2
import os
import sys

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.close()
        print('✅ Database is ready')
        break
    except psycopg2.OperationalError:
        retry_count += 1
        print(f'⏳ Database not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)
else:
    print('❌ Database connection failed after maximum retries')
    sys.exit(1)
"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
python -c "
import time
import redis
import os
import sys

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        r = redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        print('✅ Redis is ready')
        break
    except redis.ConnectionError:
        retry_count += 1
        print(f'⏳ Redis not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)
else:
    print('❌ Redis connection failed after maximum retries')
    sys.exit(1)
"

# Wait for ChromaDB to be ready
echo "⏳ Waiting for ChromaDB to be ready..."
python -c "
import time
import requests
import os
import sys

max_retries = 30
retry_count = 0
chroma_url = os.getenv('CHROMA_URL', 'http://chromadb:8001')

while retry_count < max_retries:
    try:
        response = requests.get(f'{chroma_url}/api/v1/heartbeat', timeout=5)
        if response.status_code == 200:
            print('✅ ChromaDB is ready')
            break
    except requests.RequestException:
        pass
    
    retry_count += 1
    print(f'⏳ ChromaDB not ready, retrying... ({retry_count}/{max_retries})')
    time.sleep(2)
else:
    print('❌ ChromaDB connection failed after maximum retries')
    sys.exit(1)
"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Create necessary directories
mkdir -p /app/logs /app/uploads /app/chroma_data

# Set proper permissions
chmod 755 /app/logs /app/uploads /app/chroma_data

# Start the application
echo "🎯 Starting application with supervisor..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
