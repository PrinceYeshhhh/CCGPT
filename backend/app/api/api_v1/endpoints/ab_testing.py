"""
A/B Testing endpoints for widget configurations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import structlog

from app.core.database import get_db
from app.models.user import User
from app.services.ab_testing_service import ABTestingService
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/tests")
async def get_all_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all A/B tests"""
    try:
        ab_testing_service = ABTestingService(db)
        tests = ab_testing_service.get_all_tests()
        
        return {
            "status": "success",
            "data": tests
        }
        
    except Exception as e:
        logger.error("Failed to get A/B tests", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B tests"
        )


@router.get("/tests/{test_id}")
async def get_test_details(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific A/B test"""
    try:
        ab_testing_service = ABTestingService(db)
        test_results = ab_testing_service.get_test_results(test_id)
        
        return {
            "status": "success",
            "data": test_results
        }
        
    except Exception as e:
        logger.error("Failed to get A/B test details", error=str(e), test_id=test_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B test details"
        )


@router.post("/tests")
async def create_test(
    test_id: str,
    name: str,
    variants: List[Dict[str, Any]],
    traffic_split: float = 0.5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new A/B test"""
    try:
        ab_testing_service = ABTestingService(db)
        success = ab_testing_service.create_test(test_id, name, variants, traffic_split)
        
        if success:
            return {
                "status": "success",
                "message": "A/B test created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create A/B test"
            )
        
    except Exception as e:
        logger.error("Failed to create A/B test", error=str(e), test_id=test_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create A/B test"
        )


@router.post("/tests/{test_id}/stop")
async def stop_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop an A/B test"""
    try:
        ab_testing_service = ABTestingService(db)
        success = ab_testing_service.stop_test(test_id)
        
        if success:
            return {
                "status": "success",
                "message": "A/B test stopped successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop A/B test"
            )
        
    except Exception as e:
        logger.error("Failed to stop A/B test", error=str(e), test_id=test_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop A/B test"
        )


@router.post("/tests/{test_id}/conversion")
async def track_conversion(
    test_id: str,
    conversion_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track a conversion for an A/B test"""
    try:
        ab_testing_service = ABTestingService(db)
        success = ab_testing_service.track_conversion(test_id, str(current_user.id), conversion_type)
        
        if success:
            return {
                "status": "success",
                "message": "Conversion tracked successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track conversion"
            )
        
    except Exception as e:
        logger.error("Failed to track conversion", error=str(e), test_id=test_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track conversion"
        )


@router.get("/user-variants")
async def get_user_variants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get A/B test variants for current user"""
    try:
        ab_testing_service = ABTestingService(db)
        variants = ab_testing_service.get_all_variants_for_user(str(current_user.id))
        
        return {
            "status": "success",
            "data": variants
        }
        
    except Exception as e:
        logger.error("Failed to get user variants", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user variants"
        )
