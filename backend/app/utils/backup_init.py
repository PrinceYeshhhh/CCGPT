# Backup System Initialization
# Initialize backup and disaster recovery services on application startup

import asyncio
import logging
from app.services.backup_scheduler import backup_scheduler
from app.services.disaster_recovery import disaster_recovery_service
from app.core.config import settings
from app.utils.logging_config import business_logger

logger = logging.getLogger(__name__)

async def initialize_backup_system():
    """Initialize the backup and disaster recovery system"""
    
    try:
        logger.info("Initializing backup and disaster recovery system...")
        
        # Initialize backup scheduler if enabled
        if settings.BACKUP_SCHEDULER_ENABLED:
            backup_scheduler.start()
            logger.info("Backup scheduler started")
        else:
            logger.info("Backup scheduler disabled")
        
        # Clean up old recovery operations
        await disaster_recovery_service.cleanup_old_operations()
        logger.info("Disaster recovery service initialized")
        
        logger.info("Backup and disaster recovery system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize backup system: {e}", exc_info=True)
        raise

async def shutdown_backup_system():
    """Shutdown the backup and disaster recovery system"""
    
    try:
        logger.info("Shutting down backup and disaster recovery system...")
        
        # Stop backup scheduler
        if settings.BACKUP_SCHEDULER_ENABLED:
            backup_scheduler.stop()
            logger.info("Backup scheduler stopped")
        
        logger.info("Backup and disaster recovery system shutdown completed")
        
    except Exception as e:
        logger.error(f"Failed to shutdown backup system: {e}", exc_info=True)
