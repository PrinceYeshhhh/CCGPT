#!/usr/bin/env python3
"""
Document processing worker startup script
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def start_redis_worker():
    """Start Redis worker for document processing"""
    try:
        print("Starting Redis worker for document processing...")
        
        # Start the worker process
        worker_process = subprocess.Popen([
            sys.executable, "-m", "rq", "worker", 
            "--url", os.getenv("REDIS_URL", "redis://localhost:6379"),
            "document_processing"
        ], cwd=str(backend_dir))
        
        print(f"Redis worker started with PID: {worker_process.pid}")
        return worker_process
        
    except Exception as e:
        print(f"Failed to start Redis worker: {e}")
        return None

def start_ingest_worker():
    """Start ingest worker for document processing"""
    try:
        print("Starting ingest worker...")
        
        # Start the worker process
        worker_process = subprocess.Popen([
            sys.executable, "-m", "app.worker.ingest_worker"
        ], cwd=str(backend_dir))
        
        print(f"Ingest worker started with PID: {worker_process.pid}")
        return worker_process
        
    except Exception as e:
        print(f"Failed to start ingest worker: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down workers...")
    for process in worker_processes:
        if process and process.poll() is None:
            process.terminate()
    sys.exit(0)

def main():
    """Main function to start all workers"""
    global worker_processes
    worker_processes = []
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting CustomerCareGPT Document Processing Workers...")
    print("=" * 50)
    
    # Start Redis worker
    redis_worker = start_redis_worker()
    if redis_worker:
        worker_processes.append(redis_worker)
    
    # Start ingest worker
    ingest_worker = start_ingest_worker()
    if ingest_worker:
        worker_processes.append(ingest_worker)
    
    if not worker_processes:
        print("No workers started. Exiting.")
        sys.exit(1)
    
    print("\nAll workers started successfully!")
    print("Press Ctrl+C to stop all workers.")
    print("=" * 50)
    
    try:
        # Keep the main process alive and monitor workers
        while True:
            time.sleep(1)
            
            # Check if any worker has died
            for i, process in enumerate(worker_processes):
                if process and process.poll() is not None:
                    print(f"Worker {i} has stopped unexpectedly. Restarting...")
                    if i == 0:  # Redis worker
                        new_worker = start_redis_worker()
                    else:  # Ingest worker
                        new_worker = start_ingest_worker()
                    
                    if new_worker:
                        worker_processes[i] = new_worker
                    else:
                        print(f"Failed to restart worker {i}")
                        
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
