# Backup Scheduler Service
# Automated backup scheduling and management

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import schedule
import time
from threading import Thread

from app.core.config import settings
from app.services.backup_service import backup_service, BackupType, BackupStatus
from app.utils.logging_config import business_logger

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    """Types of backup schedules"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

@dataclass
class BackupSchedule:
    """Backup schedule configuration"""
    schedule_id: str
    schedule_type: ScheduleType
    backup_type: BackupType
    components: List[str]
    retention_days: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    time_of_day: str = "02:00"  # Default 2 AM
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31

class BackupScheduler:
    """Automated backup scheduler"""
    
    def __init__(self):
        self.schedules: Dict[str, BackupSchedule] = {}
        self.scheduler_thread: Optional[Thread] = None
        self.running = False
        
        # Default schedules
        self._setup_default_schedules()
    
    def _setup_default_schedules(self):
        """Setup default backup schedules"""
        # Daily incremental backup
        daily_schedule = BackupSchedule(
            schedule_id="daily_incremental",
            schedule_type=ScheduleType.DAILY,
            backup_type=BackupType.INCREMENTAL,
            components=["database", "redis"],
            retention_days=7,
            time_of_day="02:00"
        )
        
        # Weekly full backup
        weekly_schedule = BackupSchedule(
            schedule_id="weekly_full",
            schedule_type=ScheduleType.WEEKLY,
            backup_type=BackupType.FULL,
            components=["database", "redis", "chromadb", "uploads", "config"],
            retention_days=30,
            time_of_day="03:00",
            day_of_week=0  # Sunday
        )
        
        # Monthly full backup
        monthly_schedule = BackupSchedule(
            schedule_id="monthly_full",
            schedule_type=ScheduleType.MONTHLY,
            backup_type=BackupType.FULL,
            components=["database", "redis", "chromadb", "uploads", "config"],
            retention_days=365,
            time_of_day="04:00",
            day_of_month=1
        )
        
        self.schedules = {
            daily_schedule.schedule_id: daily_schedule,
            weekly_schedule.schedule_id: weekly_schedule,
            monthly_schedule.schedule_id: monthly_schedule
        }
    
    def start(self):
        """Start the backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Backup scheduler started")
    
    def stop(self):
        """Stop the backup scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        # Setup scheduled jobs
        self._setup_scheduled_jobs()
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in backup scheduler: {e}", exc_info=True)
                time.sleep(60)
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled jobs"""
        schedule.clear()  # Clear existing jobs
        
        for schedule_config in self.schedules.values():
            if not schedule_config.enabled:
                continue
            
            if schedule_config.schedule_type == ScheduleType.DAILY:
                schedule.every().day.at(schedule_config.time_of_day).do(
                    self._execute_backup, schedule_config
                )
            elif schedule_config.schedule_type == ScheduleType.WEEKLY:
                if schedule_config.day_of_week is not None:
                    getattr(schedule.every(), self._get_weekday_name(schedule_config.day_of_week)).at(
                        schedule_config.time_of_day
                    ).do(self._execute_backup, schedule_config)
            elif schedule_config.schedule_type == ScheduleType.MONTHLY:
                # Monthly backups are handled differently
                schedule.every().day.at(schedule_config.time_of_day).do(
                    self._check_monthly_backup, schedule_config
                )
        
        logger.info(f"Setup {len(schedule.jobs)} scheduled backup jobs")
    
    def _get_weekday_name(self, day_of_week: int) -> str:
        """Convert day of week number to schedule name"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        return days[day_of_week]
    
    def _check_monthly_backup(self, schedule_config: BackupSchedule):
        """Check if monthly backup should run"""
        if schedule_config.day_of_month is None:
            return
        
        today = datetime.now()
        if today.day == schedule_config.day_of_month:
            self._execute_backup(schedule_config)
    
    def _execute_backup(self, schedule_config: BackupSchedule):
        """Execute a scheduled backup"""
        try:
            logger.info(
                "Executing scheduled backup",
                schedule_id=schedule_config.schedule_id,
                backup_type=schedule_config.backup_type.value
            )
            
            # Update last run time
            schedule_config.last_run = datetime.now()
            
            # Calculate next run time
            self._calculate_next_run(schedule_config)
            
            # Execute backup in async context
            asyncio.create_task(self._async_backup(schedule_config))
            
        except Exception as e:
            logger.error(
                f"Failed to execute scheduled backup {schedule_config.schedule_id}: {e}",
                exc_info=True
            )
    
    async def _async_backup(self, schedule_config: BackupSchedule):
        """Execute backup asynchronously"""
        try:
            metadata = await backup_service.create_backup(
                backup_type=schedule_config.backup_type,
                components=schedule_config.components,
                retention_days=schedule_config.retention_days
            )
            
            logger.info(
                "Scheduled backup completed",
                schedule_id=schedule_config.schedule_id,
                backup_id=metadata.backup_id,
                status=metadata.status.value
            )
            
        except Exception as e:
            logger.error(
                f"Scheduled backup failed {schedule_config.schedule_id}: {e}",
                exc_info=True
            )
    
    def _calculate_next_run(self, schedule_config: BackupSchedule):
        """Calculate next run time for a schedule"""
        now = datetime.now()
        
        if schedule_config.schedule_type == ScheduleType.DAILY:
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(
                hour=int(schedule_config.time_of_day.split(':')[0]),
                minute=int(schedule_config.time_of_day.split(':')[1]),
                second=0,
                microsecond=0
            )
        elif schedule_config.schedule_type == ScheduleType.WEEKLY:
            days_ahead = (schedule_config.day_of_week - now.weekday()) % 7
            if days_ahead == 0:  # Same day
                days_ahead = 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=int(schedule_config.time_of_day.split(':')[0]),
                minute=int(schedule_config.time_of_day.split(':')[1]),
                second=0,
                microsecond=0
            )
        elif schedule_config.schedule_type == ScheduleType.MONTHLY:
            # Next month, same day
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=schedule_config.day_of_month)
            else:
                next_run = now.replace(month=now.month + 1, day=schedule_config.day_of_month)
            next_run = next_run.replace(
                hour=int(schedule_config.time_of_day.split(':')[0]),
                minute=int(schedule_config.time_of_day.split(':')[1]),
                second=0,
                microsecond=0
            )
        else:
            next_run = now + timedelta(days=1)
        
        schedule_config.next_run = next_run
    
    def add_schedule(self, schedule_config: BackupSchedule):
        """Add a new backup schedule"""
        self.schedules[schedule_config.schedule_id] = schedule_config
        
        if self.running:
            self._setup_scheduled_jobs()
        
        logger.info(
            "Backup schedule added",
            schedule_id=schedule_config.schedule_id,
            schedule_type=schedule_config.schedule_type.value
        )
    
    def remove_schedule(self, schedule_id: str):
        """Remove a backup schedule"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            
            if self.running:
                self._setup_scheduled_jobs()
            
            logger.info("Backup schedule removed", schedule_id=schedule_id)
    
    def update_schedule(self, schedule_id: str, **updates):
        """Update a backup schedule"""
        if schedule_id in self.schedules:
            schedule_config = self.schedules[schedule_id]
            
            for key, value in updates.items():
                if hasattr(schedule_config, key):
                    setattr(schedule_config, key, value)
            
            if self.running:
                self._setup_scheduled_jobs()
            
            logger.info("Backup schedule updated", schedule_id=schedule_id)
    
    def get_schedules(self) -> List[BackupSchedule]:
        """Get all backup schedules"""
        return list(self.schedules.values())
    
    def get_schedule(self, schedule_id: str) -> Optional[BackupSchedule]:
        """Get a specific backup schedule"""
        return self.schedules.get(schedule_id)
    
    def enable_schedule(self, schedule_id: str):
        """Enable a backup schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = True
            
            if self.running:
                self._setup_scheduled_jobs()
            
            logger.info("Backup schedule enabled", schedule_id=schedule_id)
    
    def disable_schedule(self, schedule_id: str):
        """Disable a backup schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = False
            
            if self.running:
                self._setup_scheduled_jobs()
            
            logger.info("Backup schedule disabled", schedule_id=schedule_id)
    
    def get_next_backup_time(self) -> Optional[datetime]:
        """Get the next scheduled backup time"""
        next_times = []
        
        for schedule_config in self.schedules.values():
            if schedule_config.enabled and schedule_config.next_run:
                next_times.append(schedule_config.next_run)
        
        return min(next_times) if next_times else None
    
    def get_schedule_status(self) -> Dict:
        """Get overall schedule status"""
        enabled_schedules = sum(1 for s in self.schedules.values() if s.enabled)
        total_schedules = len(self.schedules)
        next_backup = self.get_next_backup_time()
        
        return {
            "total_schedules": total_schedules,
            "enabled_schedules": enabled_schedules,
            "disabled_schedules": total_schedules - enabled_schedules,
            "next_backup_time": next_backup.isoformat() if next_backup else None,
            "scheduler_running": self.running
        }

# Global backup scheduler instance
backup_scheduler = BackupScheduler()
