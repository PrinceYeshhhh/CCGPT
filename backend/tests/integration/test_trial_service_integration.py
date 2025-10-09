"""
Integration tests for trial service integration
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.subscriptions import Subscription
from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_workspace(db_session):
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        description="Test workspace for trial service"
    )
    db_session.add(workspace)
    db_session.commit()
    return workspace


@pytest.fixture
def test_user(db_session, test_workspace):
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        workspace_id=test_workspace.id
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_check_trial_expiration_active():
    """Test checking trial expiration for active trial"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    # Create mock database session
    mock_db = Mock()
    mock_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription
    
    service = TrialService(mock_db)
    result = service.check_trial_expiration("test-workspace")
    
    assert result["is_trial"] == True
    assert result["is_expired"] == False
    assert result["days_remaining"] == 3
    assert "Trial active" in result["message"]


def test_check_trial_expiration_expired():
    """Test checking trial expiration for expired trial"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    # Create mock database session
    mock_db = Mock()
    mock_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=datetime.utcnow() - timedelta(days=1)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_subscription
    
    service = TrialService(mock_db)
    result = service.check_trial_expiration("test-workspace")
    
    assert result["is_trial"] == True
    assert result["is_expired"] == True
    assert result["days_remaining"] == 0
    assert "Trial expired" in result["message"]
    
    # Verify subscription status was updated
    mock_db.commit.assert_called_once()


def test_check_trial_expiration_no_trial():
    """Test checking trial expiration when no trial exists"""
    from app.services.trial_service import TrialService
    
    # Create mock database session
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    service = TrialService(mock_db)
    result = service.check_trial_expiration("test-workspace")
    
    assert result["is_trial"] == False
    assert result["is_expired"] == False
    assert result["days_remaining"] == 0
    assert "No trial found" in result["message"]


def test_enforce_trial_limits_active_trial():
    """Test enforcing trial limits for active trial"""
    from app.services.trial_service import TrialService
    
    mock_db = Mock()
    service = TrialService(mock_db)
    
    with patch.object(service, 'check_trial_expiration') as mock_check:
        mock_check.return_value = {
            "is_trial": True,
            "is_expired": False,
            "days_remaining": 3
        }
        
        result = service.enforce_trial_limits("test-workspace")
        assert result == True


def test_enforce_trial_limits_expired_trial():
    """Test enforcing trial limits for expired trial"""
    from app.services.trial_service import TrialService
    
    mock_db = Mock()
    service = TrialService(mock_db)
    
    with patch.object(service, 'check_trial_expiration') as mock_check:
        mock_check.return_value = {
            "is_trial": True,
            "is_expired": True,
            "days_remaining": 0
        }
        
        result = service.enforce_trial_limits("test-workspace")
        assert result == False


def test_start_trial_success():
    """Test starting trial successfully"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing trial
    
    service = TrialService(mock_db)
    result = service.start_trial("test-workspace", "test-user")
    
    assert result["success"] == True
    assert "Trial started successfully" in result["message"]
    assert result["days_remaining"] == 7
    assert "trial_end" in result
    
    # Verify subscription was created
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_start_trial_already_exists():
    """Test starting trial when one already exists"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    existing_trial = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing"
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing_trial
    
    service = TrialService(mock_db)
    result = service.start_trial("test-workspace", "test-user")
    
    assert result["success"] == False
    assert "Trial already started for this workspace" in result["message"]


def test_get_trial_info():
    """Test getting detailed trial information"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    trial_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = trial_subscription
    
    service = TrialService(mock_db)
    
    with patch.object(service, 'check_trial_expiration') as mock_check:
        mock_check.return_value = {
            "is_trial": True,
            "is_expired": False,
            "days_remaining": 3,
            "trial_end": trial_subscription.period_end.isoformat(),
            "message": "Trial active, 3 days remaining"
        }
        
        result = service.get_trial_info("test-workspace")
        
        assert result["is_trial"] == True
        assert result["is_expired"] == False
        assert result["days_remaining"] == 3
        assert result["queries_used"] == 25
        assert result["queries_limit"] == 100
        assert result["queries_remaining"] == 75
        assert result["usage_percentage"] == 25.0


def test_get_trial_info_no_trial():
    """Test getting trial info when no trial exists"""
    from app.services.trial_service import TrialService
    
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    service = TrialService(mock_db)
    
    with patch.object(service, 'check_trial_expiration') as mock_check:
        mock_check.return_value = {
            "is_trial": False,
            "is_expired": False,
            "days_remaining": 0,
            "message": "No trial found"
        }
        
        result = service.get_trial_info("test-workspace")
        
        assert result["is_trial"] == False
        assert result["is_expired"] == False


def test_trial_service_database_error():
    """Test trial service handles database errors"""
    from app.services.trial_service import TrialService
    
    mock_db = Mock()
    mock_db.query.side_effect = Exception("Database error")
    
    service = TrialService(mock_db)
    result = service.check_trial_expiration("test-workspace")
    
    assert result["is_trial"] == False
    assert result["is_expired"] == False
    assert "Error checking trial status" in result["message"]


def test_trial_service_start_trial_database_error():
    """Test starting trial handles database errors"""
    from app.services.trial_service import TrialService
    
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.side_effect = Exception("Database error")
    
    service = TrialService(mock_db)
    result = service.start_trial("test-workspace", "test-user")
    
    assert result["success"] == False
    assert "Failed to start trial" in result["message"]
    mock_db.rollback.assert_called_once()


def test_trial_service_integration_with_quota_middleware():
    """Test trial service integration with quota middleware"""
    from app.services.trial_service import TrialService
    from app.middleware.quota_middleware import check_quota
    
    # Create test data
    mock_db = Mock()
    trial_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=50,
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = trial_subscription
    
    # Test trial service
    trial_service = TrialService(mock_db)
    trial_info = trial_service.get_trial_info("test-workspace")
    
    assert trial_info["is_trial"] == True
    assert trial_info["queries_remaining"] == 50
    
    # Test quota middleware integration
    with patch('app.middleware.quota_middleware.TrialService') as mock_trial_service_class:
        mock_trial_service = Mock()
        mock_trial_service.check_trial_expiration.return_value = {
            "is_trial": True,
            "is_expired": False,
            "days_remaining": 3
        }
        mock_trial_service_class.return_value = mock_trial_service
        
        # This would be called by quota middleware
        trial_status = trial_service.check_trial_expiration("test-workspace")
        assert trial_status["is_trial"] == True
        assert trial_status["is_expired"] == False


def test_trial_service_quota_enforcement():
    """Test trial service quota enforcement"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    trial_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=100,  # At limit
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = trial_subscription
    
    service = TrialService(mock_db)
    trial_info = service.get_trial_info("test-workspace")
    
    assert trial_info["queries_used"] == 100
    assert trial_info["queries_remaining"] == 0
    assert trial_info["usage_percentage"] == 100.0


def test_trial_service_usage_tracking():
    """Test trial service usage tracking"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    trial_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = trial_subscription
    
    service = TrialService(mock_db)
    trial_info = service.get_trial_info("test-workspace")
    
    # Test usage calculations
    assert trial_info["queries_used"] == 25
    assert trial_info["queries_limit"] == 100
    assert trial_info["queries_remaining"] == 75
    assert trial_info["usage_percentage"] == 25.0


def test_trial_service_edge_cases():
    """Test trial service edge cases"""
    from app.services.trial_service import TrialService
    from app.models.subscriptions import Subscription
    
    mock_db = Mock()
    
    # Test with None period_end
    trial_subscription = Subscription(
        workspace_id="test-workspace",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=None
    )
    mock_db.query.return_value.filter.return_value.first.return_value = trial_subscription
    
    service = TrialService(mock_db)
    result = service.check_trial_expiration("test-workspace")
    
    assert result["is_trial"] == True
    assert result["is_expired"] == False
    assert result["days_remaining"] == 0
    assert result["trial_end"] is None

