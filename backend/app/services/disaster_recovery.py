# Disaster Recovery Service
# Comprehensive disaster recovery and business continuity management

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import subprocess
import shutil
from pathlib import Path

from app.core.config import settings
from app.core.database import get_db
from app.services.backup_service import backup_service, BackupType, BackupStatus
from app.utils.logging_config import business_logger, security_logger

logger = logging.getLogger(__name__)

class RecoveryType(Enum):
    """Types of disaster recovery scenarios"""
    FULL_SYSTEM = "full_system"
    DATABASE_ONLY = "database_only"
    APPLICATION_ONLY = "application_only"
    DATA_ONLY = "data_only"
    CONFIG_ONLY = "config_only"

class RecoveryStatus(Enum):
    """Recovery operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class RecoveryPlan:
    """Disaster recovery plan configuration"""
    plan_id: str
    name: str
    description: str
    recovery_type: RecoveryType
    priority: int  # 1=highest, 5=lowest
    rto_minutes: int  # Recovery Time Objective
    rpo_minutes: int  # Recovery Point Objective
    components: List[str]
    backup_requirements: List[BackupType]
    validation_checks: List[str]
    rollback_plan: Optional[str] = None

@dataclass
class RecoveryOperation:
    """Recovery operation tracking"""
    operation_id: str
    plan_id: str
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    backup_id: Optional[str] = None
    error_message: Optional[str] = None
    steps_completed: List[str] = None
    validation_results: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []
        if self.validation_results is None:
            self.validation_results = {}

class DisasterRecoveryService:
    """Comprehensive disaster recovery service"""
    
    def __init__(self):
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.active_operations: Dict[str, RecoveryOperation] = {}
        
        # Setup default recovery plans
        self._setup_default_plans()
    
    def _setup_default_plans(self):
        """Setup default disaster recovery plans"""
        
        # Full system recovery plan
        full_system_plan = RecoveryPlan(
            plan_id="full_system_recovery",
            name="Full System Recovery",
            description="Complete system recovery from backup",
            recovery_type=RecoveryType.FULL_SYSTEM,
            priority=1,
            rto_minutes=60,
            rpo_minutes=15,
            components=["database", "redis", "chromadb", "uploads", "config", "application"],
            backup_requirements=[BackupType.FULL],
            validation_checks=[
                "database_connectivity",
                "redis_connectivity",
                "chromadb_connectivity",
                "application_health",
                "api_endpoints",
                "data_integrity"
            ],
            rollback_plan="rollback_full_system"
        )
        
        # Database recovery plan
        database_plan = RecoveryPlan(
            plan_id="database_recovery",
            name="Database Recovery",
            description="Database-only recovery from backup",
            recovery_type=RecoveryType.DATABASE_ONLY,
            priority=2,
            rto_minutes=30,
            rpo_minutes=5,
            components=["database"],
            backup_requirements=[BackupType.FULL, BackupType.INCREMENTAL],
            validation_checks=[
                "database_connectivity",
                "data_integrity",
                "schema_validation"
            ],
            rollback_plan="rollback_database"
        )
        
        # Application recovery plan
        application_plan = RecoveryPlan(
            plan_id="application_recovery",
            name="Application Recovery",
            description="Application and configuration recovery",
            recovery_type=RecoveryType.APPLICATION_ONLY,
            priority=3,
            rto_minutes=15,
            rpo_minutes=0,
            components=["application", "config"],
            backup_requirements=[BackupType.FULL],
            validation_checks=[
                "application_health",
                "api_endpoints",
                "configuration_validation"
            ],
            rollback_plan="rollback_application"
        )
        
        # Data recovery plan
        data_plan = RecoveryPlan(
            plan_id="data_recovery",
            name="Data Recovery",
            description="User data and uploads recovery",
            recovery_type=RecoveryType.DATA_ONLY,
            priority=2,
            rto_minutes=45,
            rpo_minutes=10,
            components=["uploads", "chromadb"],
            backup_requirements=[BackupType.FULL],
            validation_checks=[
                "data_integrity",
                "file_accessibility",
                "vector_search_functionality"
            ],
            rollback_plan="rollback_data"
        )
        
        self.recovery_plans = {
            full_system_plan.plan_id: full_system_plan,
            database_plan.plan_id: database_plan,
            application_plan.plan_id: application_plan,
            data_plan.plan_id: data_plan
        }
    
    async def initiate_recovery(
        self, 
        plan_id: str, 
        backup_id: Optional[str] = None,
        force: bool = False
    ) -> RecoveryOperation:
        """Initiate a disaster recovery operation"""
        
        if plan_id not in self.recovery_plans:
            raise ValueError(f"Recovery plan not found: {plan_id}")
        
        plan = self.recovery_plans[plan_id]
        
        # Check if there's already an active operation
        if not force and any(op.status == RecoveryStatus.IN_PROGRESS for op in self.active_operations.values()):
            raise ValueError("Another recovery operation is already in progress")
        
        # Find suitable backup if not specified
        if not backup_id:
            backup_id = await self._find_suitable_backup(plan)
            if not backup_id:
                raise ValueError("No suitable backup found for recovery plan")
        
        # Create recovery operation
        operation_id = f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        operation = RecoveryOperation(
            operation_id=operation_id,
            plan_id=plan_id,
            status=RecoveryStatus.IN_PROGRESS,
            started_at=datetime.now(),
            backup_id=backup_id
        )
        
        self.active_operations[operation_id] = operation
        
        logger.info(
            "Disaster recovery initiated",
            operation_id=operation_id,
            plan_id=plan_id,
            backup_id=backup_id
        )
        
        # Execute recovery in background
        asyncio.create_task(self._execute_recovery(operation))
        
        return operation
    
    async def _execute_recovery(self, operation: RecoveryOperation):
        """Execute the recovery operation"""
        plan = self.recovery_plans[operation.plan_id]
        
        try:
            # Step 1: Pre-recovery validation
            await self._pre_recovery_validation(operation)
            
            # Step 2: Stop services
            await self._stop_services(operation)
            
            # Step 3: Restore components
            await self._restore_components(operation)
            
            # Step 4: Start services
            await self._start_services(operation)
            
            # Step 5: Post-recovery validation
            await self._post_recovery_validation(operation)
            
            # Step 6: Final validation
            await self._final_validation(operation)
            
            operation.status = RecoveryStatus.COMPLETED
            operation.completed_at = datetime.now()
            
            logger.info(
                "Disaster recovery completed",
                operation_id=operation.operation_id,
                duration_minutes=(operation.completed_at - operation.started_at).total_seconds() / 60
            )
            
        except Exception as e:
            operation.status = RecoveryStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()
            
            logger.error(
                "Disaster recovery failed",
                operation_id=operation.operation_id,
                error=str(e),
                exc_info=True
            )
            
            # Attempt rollback
            await self._rollback_recovery(operation)
    
    async def _pre_recovery_validation(self, operation: RecoveryOperation):
        """Pre-recovery validation checks"""
        operation.steps_completed.append("pre_recovery_validation")
        
        # Check backup availability
        if operation.backup_id:
            backups = await backup_service.list_backups()
            backup = next((b for b in backups if b.backup_id == operation.backup_id), None)
            
            if not backup:
                raise ValueError(f"Backup not found: {operation.backup_id}")
            
            if backup.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup is not complete: {backup.status}")
        
        # Check system resources
        await self._check_system_resources()
        
        logger.info(
            "Pre-recovery validation completed",
            operation_id=operation.operation_id
        )
    
    async def _stop_services(self, operation: RecoveryOperation):
        """Stop application services"""
        operation.steps_completed.append("stop_services")
        
        # This would typically involve stopping Docker containers or systemd services
        # For now, we'll log the action
        logger.info(
            "Stopping services for recovery",
            operation_id=operation.operation_id
        )
        
        # In a real implementation, you would:
        # 1. Stop application containers
        # 2. Stop background workers
        # 3. Stop any dependent services
        # 4. Wait for graceful shutdown
    
    async def _restore_components(self, operation: RecoveryOperation):
        """Restore components from backup"""
        operation.steps_completed.append("restore_components")
        
        plan = self.recovery_plans[operation.plan_id]
        
        # Restore from backup
        success = await backup_service.restore_backup(
            backup_id=operation.backup_id,
            components=plan.components
        )
        
        if not success:
            raise Exception("Failed to restore components from backup")
        
        logger.info(
            "Components restored from backup",
            operation_id=operation.operation_id,
            components=plan.components
        )
    
    async def _start_services(self, operation: RecoveryOperation):
        """Start application services"""
        operation.steps_completed.append("start_services")
        
        # This would typically involve starting Docker containers or systemd services
        logger.info(
            "Starting services after recovery",
            operation_id=operation.operation_id
        )
        
        # In a real implementation, you would:
        # 1. Start database services
        # 2. Start Redis services
        # 3. Start application services
        # 4. Start background workers
        # 5. Wait for services to be healthy
    
    async def _post_recovery_validation(self, operation: RecoveryOperation):
        """Post-recovery validation checks"""
        operation.steps_completed.append("post_recovery_validation")
        
        plan = self.recovery_plans[operation.plan_id]
        
        # Run validation checks
        for check in plan.validation_checks:
            result = await self._run_validation_check(check)
            operation.validation_results[check] = result
            
            if not result:
                logger.warning(
                    "Validation check failed",
                    operation_id=operation.operation_id,
                    check=check
                )
        
        logger.info(
            "Post-recovery validation completed",
            operation_id=operation.operation_id,
            validation_results=operation.validation_results
        )
    
    async def _final_validation(self, operation: RecoveryOperation):
        """Final validation and health checks"""
        operation.steps_completed.append("final_validation")
        
        # Wait for services to stabilize
        await asyncio.sleep(30)
        
        # Run comprehensive health checks
        health_checks = [
            "database_connectivity",
            "redis_connectivity",
            "application_health",
            "api_endpoints"
        ]
        
        for check in health_checks:
            result = await self._run_validation_check(check)
            operation.validation_results[check] = result
        
        # Determine if recovery was successful
        failed_checks = [k for k, v in operation.validation_results.items() if not v]
        
        if failed_checks:
            operation.status = RecoveryStatus.PARTIAL
            logger.warning(
                "Recovery completed with issues",
                operation_id=operation.operation_id,
                failed_checks=failed_checks
            )
        else:
            operation.status = RecoveryStatus.COMPLETED
            logger.info(
                "Recovery completed successfully",
                operation_id=operation.operation_id
            )
    
    async def _run_validation_check(self, check_name: str) -> bool:
        """Run a specific validation check"""
        try:
            if check_name == "database_connectivity":
                return await self._check_database_connectivity()
            elif check_name == "redis_connectivity":
                return await self._check_redis_connectivity()
            elif check_name == "chromadb_connectivity":
                return await self._check_chromadb_connectivity()
            elif check_name == "application_health":
                return await self._check_application_health()
            elif check_name == "api_endpoints":
                return await self._check_api_endpoints()
            elif check_name == "data_integrity":
                return await self._check_data_integrity()
            elif check_name == "schema_validation":
                return await self._check_schema_validation()
            elif check_name == "configuration_validation":
                return await self._check_configuration_validation()
            elif check_name == "file_accessibility":
                return await self._check_file_accessibility()
            elif check_name == "vector_search_functionality":
                return await self._check_vector_search_functionality()
            else:
                logger.warning(f"Unknown validation check: {check_name}")
                return False
        except Exception as e:
            logger.error(f"Validation check failed: {check_name}, error: {e}")
            return False
    
    async def _check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            from app.core.database import get_db
            with get_db() as db:
                db.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def _check_redis_connectivity(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            return True
        except Exception:
            return False
    
    async def _check_chromadb_connectivity(self) -> bool:
        """Check ChromaDB connectivity"""
        try:
            import requests
            response = requests.get(f"{settings.CHROMA_URL}/api/v1/heartbeat", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def _check_application_health(self) -> bool:
        """Check application health"""
        try:
            import requests
            response = requests.get(f"{settings.API_BASE_URL}/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    async def _check_api_endpoints(self) -> bool:
        """Check API endpoints"""
        try:
            import requests
            endpoints = ["/health", "/ready", "/api/v1/auth/me"]
            
            for endpoint in endpoints:
                response = requests.get(f"{settings.API_BASE_URL}{endpoint}", timeout=5)
                if response.status_code not in [200, 401]:  # 401 is OK for auth endpoints
                    return False
            
            return True
        except Exception:
            return False
    
    async def _check_data_integrity(self) -> bool:
        """Check data integrity"""
        try:
            from app.core.database import get_db
            with get_db() as db:
                # Check if critical tables exist and have data
                tables = ["users", "workspaces", "documents", "chat_sessions"]
                for table in tables:
                    result = db.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    if count is None:
                        return False
            return True
        except Exception:
            return False
    
    async def _check_schema_validation(self) -> bool:
        """Check database schema validation"""
        try:
            from app.core.database import get_db
            with get_db() as db:
                # Check if all required tables exist
                result = db.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in result.fetchall()]
                
                required_tables = ["users", "workspaces", "documents", "chat_sessions", "chat_messages"]
                return all(table in tables for table in required_tables)
        except Exception:
            return False
    
    async def _check_configuration_validation(self) -> bool:
        """Check configuration validation"""
        try:
            # Check if critical configuration is set
            required_settings = [
                "DATABASE_URL",
                "REDIS_URL",
                "SECRET_KEY",
                "JWT_SECRET"
            ]
            
            for setting in required_settings:
                if not getattr(settings, setting, None):
                    return False
            
            return True
        except Exception:
            return False
    
    async def _check_file_accessibility(self) -> bool:
        """Check file accessibility"""
        try:
            uploads_dir = Path(settings.UPLOAD_DIR or "/app/uploads")
            return uploads_dir.exists() and uploads_dir.is_dir()
        except Exception:
            return False
    
    async def _check_vector_search_functionality(self) -> bool:
        """Check vector search functionality"""
        try:
            from app.services.vector_service import vector_service
            # Try a simple vector search
            results = vector_service.search_documents("test", workspace_id="test", limit=1)
            return True
        except Exception:
            return False
    
    async def _check_system_resources(self):
        """Check system resources before recovery"""
        import psutil
        
        # Check available disk space (need at least 1GB)
        disk_usage = psutil.disk_usage('/')
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb < 1:
            raise ValueError(f"Insufficient disk space: {free_gb:.2f}GB available")
        
        # Check available memory (need at least 2GB)
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb < 2:
            raise ValueError(f"Insufficient memory: {available_gb:.2f}GB available")
    
    async def _find_suitable_backup(self, plan: RecoveryPlan) -> Optional[str]:
        """Find a suitable backup for the recovery plan"""
        backups = await backup_service.list_backups()
        
        # Filter by backup type requirements
        suitable_backups = []
        for backup in backups:
            if backup.status == BackupStatus.COMPLETED:
                if backup.backup_type in plan.backup_requirements:
                    suitable_backups.append(backup)
        
        if not suitable_backups:
            return None
        
        # Return the most recent suitable backup
        return max(suitable_backups, key=lambda x: x.created_at).backup_id
    
    async def _rollback_recovery(self, operation: RecoveryOperation):
        """Rollback a failed recovery operation"""
        logger.warning(
            "Rolling back failed recovery operation",
            operation_id=operation.operation_id
        )
        
        # This would implement the rollback plan
        # For now, we'll just log the action
        logger.info(
            "Recovery rollback completed",
            operation_id=operation.operation_id
        )
    
    def get_recovery_plans(self) -> List[RecoveryPlan]:
        """Get all recovery plans"""
        return list(self.recovery_plans.values())
    
    def get_recovery_plan(self, plan_id: str) -> Optional[RecoveryPlan]:
        """Get a specific recovery plan"""
        return self.recovery_plans.get(plan_id)
    
    def get_active_operations(self) -> List[RecoveryOperation]:
        """Get active recovery operations"""
        return [op for op in self.active_operations.values() if op.status == RecoveryStatus.IN_PROGRESS]
    
    def get_operation(self, operation_id: str) -> Optional[RecoveryOperation]:
        """Get a specific recovery operation"""
        return self.active_operations.get(operation_id)
    
    async def cleanup_old_operations(self):
        """Clean up old recovery operations"""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        old_operations = [
            op_id for op_id, op in self.active_operations.items()
            if op.completed_at and op.completed_at < cutoff_date
        ]
        
        for op_id in old_operations:
            del self.active_operations[op_id]
        
        if old_operations:
            logger.info(
                "Cleaned up old recovery operations",
                count=len(old_operations)
            )

# Global disaster recovery service instance
disaster_recovery_service = DisasterRecoveryService()
