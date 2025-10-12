#!/usr/bin/env python3
# Backup Management Script for CustomerCareGPT
# Command-line tool for backup and disaster recovery operations

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.backup_service import backup_service, BackupType, BackupStatus
from app.services.backup_scheduler import backup_scheduler
from app.services.disaster_recovery import disaster_recovery_service, RecoveryType
from app.core.config import settings
from app.utils.logging_config import business_logger

class BackupManager:
    """Command-line backup management tool"""
    
    def __init__(self):
        self.backup_service = backup_service
        self.scheduler = backup_scheduler
        self.disaster_recovery = disaster_recovery_service
    
    async def create_backup(self, args):
        """Create a new backup"""
        print(f"Creating {args.type} backup...")
        
        try:
            metadata = await self.backup_service.create_backup(
                backup_type=BackupType(args.type),
                components=args.components,
                retention_days=args.retention
            )
            
            print(f"✅ Backup created successfully!")
            print(f"   Backup ID: {metadata.backup_id}")
            print(f"   Status: {metadata.status.value}")
            print(f"   Size: {metadata.size_bytes:,} bytes")
            print(f"   Components: {', '.join(metadata.components)}")
            
            if metadata.error_message:
                print(f"   Error: {metadata.error_message}")
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            sys.exit(1)
    
    async def list_backups(self, args):
        """List available backups"""
        print("Available backups:")
        print("-" * 80)
        
        try:
            backups = await self.backup_service.list_backups()
            
            if not backups:
                print("No backups found.")
                return
            
            # Apply filters
            if args.status:
                backups = [b for b in backups if b.status.value == args.status]
            
            if args.type:
                backups = [b for b in backups if b.backup_type.value == args.type]
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply limit
            if args.limit:
                backups = backups[:args.limit]
            
            for backup in backups:
                status_icon = "✅" if backup.status == BackupStatus.COMPLETED else "❌"
                size_mb = backup.size_bytes / (1024 * 1024)
                
                print(f"{status_icon} {backup.backup_id}")
                print(f"   Type: {backup.backup_type.value}")
                print(f"   Status: {backup.status.value}")
                print(f"   Created: {backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Size: {size_mb:.2f} MB")
                print(f"   Components: {', '.join(backup.components)}")
                
                if backup.completed_at:
                    duration = (backup.completed_at - backup.created_at).total_seconds()
                    print(f"   Duration: {duration:.1f}s")
                
                if backup.error_message:
                    print(f"   Error: {backup.error_message}")
                
                print()
            
            print(f"Total: {len(backups)} backups")
            
        except Exception as e:
            print(f"❌ Failed to list backups: {e}")
            sys.exit(1)
    
    async def restore_backup(self, args):
        """Restore from backup"""
        print(f"Restoring from backup: {args.backup_id}")
        
        if not args.force:
            response = input("⚠️  This will overwrite existing data. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Restore cancelled.")
                return
        
        try:
            success = await self.backup_service.restore_backup(
                backup_id=args.backup_id,
                components=args.components
            )
            
            if success:
                print("✅ Backup restored successfully!")
            else:
                print("❌ Backup restore failed!")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Backup restore failed: {e}")
            sys.exit(1)
    
    async def delete_backup(self, args):
        """Delete a backup"""
        print(f"Deleting backup: {args.backup_id}")
        
        if not args.force:
            response = input("⚠️  This will permanently delete the backup. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Delete cancelled.")
                return
        
        try:
            success = await self.backup_service.delete_backup(args.backup_id)
            
            if success:
                print("✅ Backup deleted successfully!")
            else:
                print("❌ Backup deletion failed!")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Backup deletion failed: {e}")
            sys.exit(1)
    
    async def cleanup_backups(self, args):
        """Clean up old backups"""
        print("Cleaning up old backups...")
        
        try:
            await self.backup_service.cleanup_old_backups()
            print("✅ Old backups cleaned up successfully!")
            
        except Exception as e:
            print(f"❌ Backup cleanup failed: {e}")
            sys.exit(1)
    
    async def schedule_management(self, args):
        """Manage backup schedules"""
        if args.action == "list":
            schedules = self.scheduler.get_schedules()
            
            print("Backup Schedules:")
            print("-" * 60)
            
            for schedule in schedules:
                status = "Enabled" if schedule.enabled else "Disabled"
                next_run = schedule.next_run.strftime('%Y-%m-%d %H:%M:%S') if schedule.next_run else "Not scheduled"
                
                print(f"📅 {schedule.schedule_id}")
                print(f"   Type: {schedule.schedule_type.value}")
                print(f"   Backup Type: {schedule.backup_type.value}")
                print(f"   Status: {status}")
                print(f"   Next Run: {next_run}")
                print(f"   Components: {', '.join(schedule.components)}")
                print()
        
        elif args.action == "enable":
            self.scheduler.enable_schedule(args.schedule_id)
            print(f"✅ Schedule {args.schedule_id} enabled")
        
        elif args.action == "disable":
            self.scheduler.disable_schedule(args.schedule_id)
            print(f"✅ Schedule {args.schedule_id} disabled")
        
        elif args.action == "status":
            status = self.scheduler.get_schedule_status()
            
            print("Scheduler Status:")
            print("-" * 40)
            print(f"Total Schedules: {status['total_schedules']}")
            print(f"Enabled Schedules: {status['enabled_schedules']}")
            print(f"Disabled Schedules: {status['disabled_schedules']}")
            print(f"Scheduler Running: {status['scheduler_running']}")
            
            if status['next_backup_time']:
                print(f"Next Backup: {status['next_backup_time']}")
            else:
                print("Next Backup: Not scheduled")
    
    async def disaster_recovery(self, args):
        """Disaster recovery operations"""
        if args.action == "plans":
            plans = self.disaster_recovery.get_recovery_plans()
            
            print("Disaster Recovery Plans:")
            print("-" * 60)
            
            for plan in plans:
                print(f"🔄 {plan.name}")
                print(f"   ID: {plan.plan_id}")
                print(f"   Type: {plan.recovery_type.value}")
                print(f"   Priority: {plan.priority}")
                print(f"   RTO: {plan.rto_minutes} minutes")
                print(f"   RPO: {plan.rpo_minutes} minutes")
                print(f"   Components: {', '.join(plan.components)}")
                print()
        
        elif args.action == "initiate":
            print(f"Initiating recovery with plan: {args.plan_id}")
            
            if not args.force:
                response = input("⚠️  This will restore the system from backup. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Recovery cancelled.")
                    return
            
            try:
                operation = await self.disaster_recovery.initiate_recovery(
                    plan_id=args.plan_id,
                    backup_id=args.backup_id,
                    force=args.force
                )
                
                print(f"✅ Recovery initiated!")
                print(f"   Operation ID: {operation.operation_id}")
                print(f"   Status: {operation.status.value}")
                print(f"   Started: {operation.started_at}")
                
            except Exception as e:
                print(f"❌ Recovery initiation failed: {e}")
                sys.exit(1)
        
        elif args.action == "status":
            operations = self.disaster_recovery.get_active_operations()
            
            print("Active Recovery Operations:")
            print("-" * 60)
            
            if not operations:
                print("No active recovery operations.")
                return
            
            for operation in operations:
                print(f"🔄 {operation.operation_id}")
                print(f"   Plan: {operation.plan_id}")
                print(f"   Status: {operation.status.value}")
                print(f"   Started: {operation.started_at}")
                print(f"   Steps Completed: {len(operation.steps_completed)}")
                print()
    
    async def health_check(self, args):
        """Check backup system health"""
        print("Backup System Health Check:")
        print("-" * 40)
        
        try:
            # Check backup directory
            backup_dir = self.backup_service.backup_dir
            print(f"Backup Directory: {backup_dir}")
            print(f"  Exists: {'✅' if backup_dir.exists() else '❌'}")
            print(f"  Writable: {'✅' if backup_dir.is_dir() and backup_dir.stat().st_mode & 0o200 else '❌'}")
            
            # Check S3 connectivity
            if self.backup_service.s3_client:
                print(f"S3 Storage: {'✅' if self.backup_service.s3_bucket else '❌'}")
            else:
                print("S3 Storage: Not configured")
            
            # Check recent backups
            backups = await self.backup_service.list_backups()
            recent_backups = [b for b in backups if b.created_at > datetime.now() - timedelta(days=7)]
            
            print(f"Recent Backups (7 days): {len(recent_backups)}")
            
            if recent_backups:
                latest = max(recent_backups, key=lambda x: x.created_at)
                print(f"Latest Backup: {latest.backup_id}")
                print(f"  Status: {latest.status.value}")
                print(f"  Created: {latest.created_at}")
                print(f"  Size: {latest.size_bytes:,} bytes")
            
            # Check scheduler status
            scheduler_status = self.scheduler.get_schedule_status()
            print(f"Scheduler Running: {'✅' if scheduler_status['scheduler_running'] else '❌'}")
            print(f"Enabled Schedules: {scheduler_status['enabled_schedules']}")
            
            print("\n✅ Health check completed!")
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CustomerCareGPT Backup Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create backup command
    create_parser = subparsers.add_parser("create", help="Create a new backup")
    create_parser.add_argument("--type", choices=["full", "incremental", "differential"], default="full")
    create_parser.add_argument("--components", nargs="+", 
                             choices=["database", "redis", "chromadb", "uploads", "config"],
                             default=["database", "redis", "chromadb", "uploads", "config"])
    create_parser.add_argument("--retention", type=int, default=30)
    
    # List backups command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--status", choices=["pending", "in_progress", "completed", "failed"])
    list_parser.add_argument("--type", choices=["full", "incremental", "differential"])
    list_parser.add_argument("--limit", type=int, default=20)
    
    # Restore backup command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_id", help="Backup ID to restore")
    restore_parser.add_argument("--components", nargs="+",
                               choices=["database", "redis", "chromadb", "uploads", "config"])
    restore_parser.add_argument("--force", action="store_true")
    
    # Delete backup command
    delete_parser = subparsers.add_parser("delete", help="Delete a backup")
    delete_parser.add_argument("backup_id", help="Backup ID to delete")
    delete_parser.add_argument("--force", action="store_true")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    
    # Schedule management commands
    schedule_parser = subparsers.add_parser("schedule", help="Manage backup schedules")
    schedule_parser.add_argument("action", choices=["list", "enable", "disable", "status"])
    schedule_parser.add_argument("--schedule-id", help="Schedule ID for enable/disable")
    
    # Disaster recovery commands
    dr_parser = subparsers.add_parser("disaster-recovery", help="Disaster recovery operations")
    dr_parser.add_argument("action", choices=["plans", "initiate", "status"])
    dr_parser.add_argument("--plan-id", help="Recovery plan ID")
    dr_parser.add_argument("--backup-id", help="Backup ID to restore from")
    dr_parser.add_argument("--force", action="store_true")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check backup system health")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create backup manager and run command
    manager = BackupManager()
    
    try:
        if args.command == "create":
            asyncio.run(manager.create_backup(args))
        elif args.command == "list":
            asyncio.run(manager.list_backups(args))
        elif args.command == "restore":
            asyncio.run(manager.restore_backup(args))
        elif args.command == "delete":
            asyncio.run(manager.delete_backup(args))
        elif args.command == "cleanup":
            asyncio.run(manager.cleanup_backups(args))
        elif args.command == "schedule":
            asyncio.run(manager.schedule_management(args))
        elif args.command == "disaster-recovery":
            asyncio.run(manager.disaster_recovery(args))
        elif args.command == "health":
            asyncio.run(manager.health_check(args))
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
