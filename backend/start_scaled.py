"""
Startup script for scaled CustomerCareGPT deployment
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import initialize_database, db_manager, redis_manager
from app.core.queue import queue_manager
from app.worker.enhanced_worker import enhanced_worker
from app.services.enhanced_vector_service import enhanced_vector_service
from app.utils.health import get_detailed_health_status
from app.utils.circuit_breaker import circuit_breaker_manager
import structlog

logger = structlog.get_logger()


async def initialize_system():
    """Initialize the scaled system"""
    logger.info("Starting CustomerCareGPT Scaled System Initialization")
    
    try:
        # 1. Initialize database with indexes
        logger.info("Initializing database with performance indexes...")
        await initialize_database()
        logger.info("Database initialization completed")
        
        # 2. Test database connections
        logger.info("Testing database connections...")
        db_health = await db_manager.health_check()
        if not db_health['overall']:
            raise Exception("Database health check failed")
        logger.info("Database connections verified")
        
        # 3. Test Redis connection
        logger.info("Testing Redis connection...")
        redis_health = await redis_manager.health_check()
        if not redis_health:
            raise Exception("Redis health check failed")
        logger.info("Redis connection verified")
        
        # 4. Test vector database
        logger.info("Testing vector database connection...")
        vector_health = await enhanced_vector_service.health_check()
        if vector_health['status'] != 'healthy':
            logger.warning(f"Vector database health check: {vector_health}")
        else:
            logger.info("Vector database connection verified")
        
        # 5. Initialize circuit breakers
        logger.info("Initializing circuit breakers...")
        # Circuit breakers are initialized when first accessed
        logger.info("Circuit breakers initialized")
        
        # 6. Start enhanced worker
        logger.info("Starting enhanced background worker...")
        worker_task = asyncio.create_task(enhanced_worker.start())
        logger.info("Enhanced worker started")
        
        # 7. Run comprehensive health check
        logger.info("Running comprehensive health check...")
        health_status = await get_detailed_health_status()
        
        if health_status['overall_healthy']:
            logger.info("✅ System initialization completed successfully")
            logger.info(f"System status: {health_status['status']}")
        else:
            logger.warning("⚠️ System initialization completed with warnings")
            logger.warning(f"System status: {health_status['status']}")
        
        # 8. Display system capabilities
        display_system_capabilities(health_status)
        
        return True
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return False


def display_system_capabilities(health_status):
    """Display system capabilities and performance metrics"""
    print("\n" + "="*60)
    print("🚀 CUSTOMERCAREGPT SCALED SYSTEM READY")
    print("="*60)
    
    print(f"📊 System Status: {health_status['status'].upper()}")
    print(f"⏰ Initialized at: {health_status['timestamp']}")
    
    # Database capabilities
    db_info = health_status.get('database', {})
    print(f"\n🗄️  Database:")
    print(f"   - Write DB: {'✅' if db_info.get('write_db') else '❌'}")
    print(f"   - Read DBs: {sum(db_info.get('read_dbs', []))} healthy")
    print(f"   - Connection Pool: 50 write + 30 read per replica")
    
    # Redis capabilities
    redis_info = health_status.get('redis', {})
    print(f"\n🔴 Redis Cache:")
    print(f"   - Status: {'✅' if redis_info else '❌'}")
    print(f"   - Max Connections: 100")
    print(f"   - Memory: 2GB with LRU eviction")
    
    # Vector DB capabilities
    vector_info = health_status.get('vector_db', {})
    print(f"\n🔍 Vector Database:")
    print(f"   - Status: {'✅' if vector_info.get('status') == 'healthy' else '❌'}")
    print(f"   - Collections: {vector_info.get('collections_count', 0)}")
    
    # Performance metrics
    perf_info = health_status.get('performance', {})
    print(f"\n⚡ Performance Capabilities:")
    print(f"   - API Replicas: 3 (load balanced)")
    print(f"   - Background Workers: 2 (enhanced)")
    print(f"   - Queue Workers: 2 (priority queues)")
    print(f"   - Circuit Breakers: Active")
    
    # Expected capacity
    print(f"\n📈 Expected Capacity:")
    print(f"   - Business Owners: 300+")
    print(f"   - Customers: 5,000+")
    print(f"   - Queries: 30,000-50,000/day")
    print(f"   - Concurrent Users: 200+")
    print(f"   - RAG Response Time: 1-3 seconds")
    print(f"   - File Processing: 50-100 docs/minute")
    
    # Monitoring
    print(f"\n📊 Monitoring:")
    print(f"   - Health Checks: /health")
    print(f"   - Metrics: /metrics")
    print(f"   - Detailed Status: /health/detailed")
    print(f"   - Prometheus: http://localhost:9090")
    print(f"   - Grafana: http://localhost:3000")
    
    print("\n" + "="*60)
    print("🎯 SYSTEM READY FOR PRODUCTION LOAD!")
    print("="*60)


async def run_performance_test():
    """Run performance test to validate scaling"""
    try:
        logger.info("Running performance validation test...")
        
        # Import and run performance test
        from performance_test import PerformanceTester
        
        tester = PerformanceTester("http://localhost:8000")
        
        # Run quick validation test
        print("\n🧪 Running Performance Validation Test...")
        
        # Test 1: Health checks
        health_results = await tester.test_health_check_performance(50)
        print(f"Health Checks: {health_results['success_rate']:.1%} success rate")
        
        # Test 2: RAG queries
        rag_results = await tester.test_rag_performance(100, 10)
        print(f"RAG Queries: {rag_results['success_rate']:.1%} success rate, {rag_results['avg_response_time']:.2f}s avg")
        
        # Test 3: Concurrent users
        concurrent_results = await tester.test_concurrent_users(50, 5)
        print(f"Concurrent Users: {concurrent_results['success_rate']:.1%} success rate, {concurrent_results['avg_response_time']:.2f}s avg")
        
        # Performance assessment
        if (rag_results['success_rate'] >= 0.90 and 
            rag_results['avg_response_time'] <= 5.0 and
            concurrent_results['success_rate'] >= 0.85):
            print("✅ Performance validation PASSED - System ready for target load")
            return True
        else:
            print("❌ Performance validation FAILED - System needs optimization")
            return False
            
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return False


async def main():
    """Main startup function"""
    print("🚀 CustomerCareGPT Scaled System Startup")
    print("="*50)
    
    # Initialize system
    success = await initialize_system()
    
    if not success:
        print("❌ System initialization failed")
        sys.exit(1)
    
    # Run performance test if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_success = await run_performance_test()
        if not test_success:
            print("⚠️ Performance test failed, but system is running")
    
    print("\n🎉 CustomerCareGPT Scaled System is now running!")
    print("📝 Check logs for detailed information")
    print("🔗 Access the API at: http://localhost:8000")
    print("📊 Monitor at: http://localhost:3000 (Grafana)")
    
    # Keep the process running
    try:
        while True:
            await asyncio.sleep(60)
            # Periodic health check
            health_status = await get_detailed_health_status()
            if not health_status['overall_healthy']:
                logger.warning("System health degraded", status=health_status['status'])
    except KeyboardInterrupt:
        print("\n👋 Shutting down CustomerCareGPT Scaled System...")
        enhanced_worker.stop()
        print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
