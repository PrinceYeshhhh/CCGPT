# Disaster Recovery API Endpoints
# Administrative endpoints for disaster recovery management

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.disaster_recovery import (
    disaster_recovery_service, 
    RecoveryType, 
    RecoveryStatus,
    RecoveryPlan,
    RecoveryOperation
)
from app.utils.logging_config import business_logger, security_logger
from app.utils.error_handling import CustomError, AuthorizationError

router = APIRouter()

class RecoveryPlanResponse(BaseModel):
    """Response model for recovery plans"""
    plan_id: str
    name: str
    description: str
    recovery_type: str
    priority: int
    rto_minutes: int
    rpo_minutes: int
    components: List[str]
    backup_requirements: List[str]
    validation_checks: List[str]
    rollback_plan: Optional[str] = None

class RecoveryOperationResponse(BaseModel):
    """Response model for recovery operations"""
    operation_id: str
    plan_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    backup_id: Optional[str] = None
    error_message: Optional[str] = None
    steps_completed: List[str] = []
    validation_results: dict = {}

class InitiateRecoveryRequest(BaseModel):
    """Request model for initiating recovery"""
    plan_id: str
    backup_id: Optional[str] = Field(
        default=None,
        description="Specific backup to restore from (optional)"
    )
    force: bool = Field(
        default=False,
        description="Force recovery even if another operation is in progress"
    )

class RecoveryStatusResponse(BaseModel):
    """Response model for recovery status"""
    total_plans: int
    active_operations: int
    last_recovery: Optional[datetime] = None
    system_health: dict = {}

@router.get("/plans", response_model=List[RecoveryPlanResponse])
async def get_recovery_plans(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all available disaster recovery plans.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        plans = disaster_recovery_service.get_recovery_plans()
        
        return [
            RecoveryPlanResponse(
                plan_id=plan.plan_id,
                name=plan.name,
                description=plan.description,
                recovery_type=plan.recovery_type.value,
                priority=plan.priority,
                rto_minutes=plan.rto_minutes,
                rpo_minutes=plan.rpo_minutes,
                components=plan.components,
                backup_requirements=[bt.value for bt in plan.backup_requirements],
                validation_checks=plan.validation_checks,
                rollback_plan=plan.rollback_plan
            )
            for plan in plans
        ]
        
    except Exception as e:
        business_logger.error(
            "Failed to get recovery plans",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery plans: {str(e)}"
        )

@router.get("/plans/{plan_id}", response_model=RecoveryPlanResponse)
async def get_recovery_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get details of a specific recovery plan.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        plan = disaster_recovery_service.get_recovery_plan(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery plan not found"
            )
        
        return RecoveryPlanResponse(
            plan_id=plan.plan_id,
            name=plan.name,
            description=plan.description,
            recovery_type=plan.recovery_type.value,
            priority=plan.priority,
            rto_minutes=plan.rto_minutes,
            rpo_minutes=plan.rpo_minutes,
            components=plan.components,
            backup_requirements=[bt.value for bt in plan.backup_requirements],
            validation_checks=plan.validation_checks,
            rollback_plan=plan.rollback_plan
        )
        
    except HTTPException:
        raise
    except Exception as e:
        business_logger.error(
            "Failed to get recovery plan",
            plan_id=plan_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery plan: {str(e)}"
        )

@router.post("/initiate", response_model=RecoveryOperationResponse)
async def initiate_recovery(
    request: InitiateRecoveryRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Initiate a disaster recovery operation.
    
    WARNING: This will restore the system from backup!
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="initiate_recovery",
        plan_id=request.plan_id,
        backup_id=request.backup_id,
        force=request.force
    )
    
    try:
        operation = await disaster_recovery_service.initiate_recovery(
            plan_id=request.plan_id,
            backup_id=request.backup_id,
            force=request.force
        )
        
        business_logger.info(
            "Disaster recovery initiated",
            operation_id=operation.operation_id,
            plan_id=request.plan_id,
            user_id=str(current_user.id)
        )
        
        return RecoveryOperationResponse(
            operation_id=operation.operation_id,
            plan_id=operation.plan_id,
            status=operation.status.value,
            started_at=operation.started_at,
            completed_at=operation.completed_at,
            backup_id=operation.backup_id,
            error_message=operation.error_message,
            steps_completed=operation.steps_completed,
            validation_results=operation.validation_results
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        business_logger.error(
            "Failed to initiate recovery",
            plan_id=request.plan_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate recovery: {str(e)}"
        )

@router.get("/operations", response_model=List[RecoveryOperationResponse])
async def get_recovery_operations(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all recovery operations.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        operations = disaster_recovery_service.get_active_operations()
        
        return [
            RecoveryOperationResponse(
                operation_id=op.operation_id,
                plan_id=op.plan_id,
                status=op.status.value,
                started_at=op.started_at,
                completed_at=op.completed_at,
                backup_id=op.backup_id,
                error_message=op.error_message,
                steps_completed=op.steps_completed,
                validation_results=op.validation_results
            )
            for op in operations
        ]
        
    except Exception as e:
        business_logger.error(
            "Failed to get recovery operations",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery operations: {str(e)}"
        )

@router.get("/operations/{operation_id}", response_model=RecoveryOperationResponse)
async def get_recovery_operation(
    operation_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get details of a specific recovery operation.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        operation = disaster_recovery_service.get_operation(operation_id)
        
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery operation not found"
            )
        
        return RecoveryOperationResponse(
            operation_id=operation.operation_id,
            plan_id=operation.plan_id,
            status=operation.status.value,
            started_at=operation.started_at,
            completed_at=operation.completed_at,
            backup_id=operation.backup_id,
            error_message=operation.error_message,
            steps_completed=operation.steps_completed,
            validation_results=operation.validation_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        business_logger.error(
            "Failed to get recovery operation",
            operation_id=operation_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery operation: {str(e)}"
        )

@router.get("/status", response_model=RecoveryStatusResponse)
async def get_recovery_status(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get disaster recovery system status.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        plans = disaster_recovery_service.get_recovery_plans()
        active_operations = disaster_recovery_service.get_active_operations()
        
        # Get last recovery time
        last_recovery = None
        if active_operations:
            last_recovery = max(op.started_at for op in active_operations)
        
        # Get system health
        system_health = {
            "database_connectivity": await disaster_recovery_service._check_database_connectivity(),
            "redis_connectivity": await disaster_recovery_service._check_redis_connectivity(),
            "chromadb_connectivity": await disaster_recovery_service._check_chromadb_connectivity(),
            "application_health": await disaster_recovery_service._check_application_health()
        }
        
        return RecoveryStatusResponse(
            total_plans=len(plans),
            active_operations=len(active_operations),
            last_recovery=last_recovery,
            system_health=system_health
        )
        
    except Exception as e:
        business_logger.error(
            "Failed to get recovery status",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery status: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_operations(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Clean up old recovery operations.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="cleanup_recovery_operations"
    )
    
    try:
        await disaster_recovery_service.cleanup_old_operations()
        
        business_logger.info(
            "Recovery operations cleanup completed",
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Old recovery operations cleaned up successfully"
            }
        )
        
    except Exception as e:
        business_logger.error(
            "Recovery operations cleanup failed",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recovery operations cleanup failed: {str(e)}"
        )

@router.post("/test/{plan_id}")
async def test_recovery_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Test a recovery plan without actually performing recovery.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for disaster recovery operations")
    
    try:
        plan = disaster_recovery_service.get_recovery_plan(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recovery plan not found"
            )
        
        # Run validation checks without actually performing recovery
        validation_results = {}
        
        for check in plan.validation_checks:
            result = await disaster_recovery_service._run_validation_check(check)
            validation_results[check] = result
        
        business_logger.info(
            "Recovery plan test completed",
            plan_id=plan_id,
            validation_results=validation_results,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Recovery plan test completed",
                "plan_id": plan_id,
                "validation_results": validation_results,
                "overall_status": "passed" if all(validation_results.values()) else "failed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        business_logger.error(
            "Recovery plan test failed",
            plan_id=plan_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recovery plan test failed: {str(e)}"
        )
