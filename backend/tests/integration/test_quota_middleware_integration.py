"""
Integration tests for quota middleware enforcement
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
        description="Test workspace for quota testing"
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


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


def test_quota_check_within_limits(client, db_session, test_user, auth_token):
    """Test quota check when within limits"""
    # Create subscription with remaining quota
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        mock_check_quota.return_value = subscription
        
        # Test an endpoint that uses quota middleware
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should not be blocked by quota
        assert response.status_code != 402


def test_quota_check_exceeded(client, db_session, test_user, auth_token):
    """Test quota check when quota is exceeded"""
    # Create subscription with exceeded quota
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="starter",
        status="active",
        monthly_query_quota=100,
        queries_this_period=100  # At limit
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        from app.middleware.quota_middleware import QuotaExceededException
        mock_check_quota.side_effect = QuotaExceededException(
            "Quota exceeded",
            {
                "tier": "starter",
                "status": "active",
                "quota_used": 100,
                "quota_limit": 100,
                "remaining": 0,
                "usage_percentage": 100.0
            }
        )
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 402
        data = response.json()
        assert data["code"] == "quota_exceeded"
        assert "Quota exceeded" in data["message"]


def test_quota_check_trial_user(client, db_session, test_user, auth_token):
    """Test quota check for trial user"""
    # Create trial subscription
    trial_subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=50,
        period_end=datetime.utcnow() + timedelta(days=3)
    )
    db_session.add(trial_subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        mock_check_quota.return_value = trial_subscription
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Trial user should be allowed
        assert response.status_code != 402


def test_quota_check_expired_trial(client, db_session, test_user, auth_token):
    """Test quota check for expired trial"""
    # Create expired trial subscription
    expired_trial = Subscription(
        workspace_id=test_user.workspace_id,
        tier="free_trial",
        status="expired",
        monthly_query_quota=100,
        queries_this_period=50,
        period_end=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(expired_trial)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        from app.middleware.quota_middleware import QuotaExceededException
        mock_check_quota.side_effect = QuotaExceededException(
            "Your free trial has expired. Please subscribe to continue.",
            {"tier": "free_trial", "status": "expired", "trial_expired": True}
        )
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 402
        data = response.json()
        assert "trial has expired" in data["message"]


def test_quota_check_no_subscription(client, db_session, test_user, auth_token):
    """Test quota check when no subscription exists"""
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        from app.middleware.quota_middleware import QuotaExceededException
        mock_check_quota.side_effect = QuotaExceededException(
            "No active subscription found. Please subscribe to continue.",
            {"tier": "none", "status": "inactive"}
        )
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 402
        data = response.json()
        assert "No active subscription found" in data["message"]


def test_quota_increment_usage_success(client, db_session, test_user, auth_token):
    """Test incrementing usage after successful operation"""
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota, \
         patch('app.middleware.quota_middleware.increment_usage') as mock_increment:
        
        mock_check_quota.return_value = subscription
        mock_increment.return_value = True
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should call increment_usage
        mock_increment.assert_called_once()


def test_quota_increment_usage_failure(client, db_session, test_user, auth_token):
    """Test incrementing usage when it fails"""
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota, \
         patch('app.middleware.quota_middleware.increment_usage') as mock_increment:
        
        mock_check_quota.return_value = subscription
        mock_increment.side_effect = Exception("Database error")
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should handle the error gracefully
        assert response.status_code in [200, 500]


def test_get_quota_info_free_tier(client, db_session, test_user, auth_token):
    """Test getting quota info for free tier user"""
    with patch('app.middleware.quota_middleware.get_quota_info') as mock_get_quota:
        mock_get_quota.return_value = {
            "tier": "free",
            "status": "active",
            "quota_used": 0,
            "quota_limit": 100,
            "remaining": 100,
            "usage_percentage": 0.0,
            "is_unlimited": False,
            "documents_limit": 1,
            "storage_limit": 10485760  # 10MB
        }
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should work for free tier
        assert response.status_code != 402


def test_get_quota_info_pro_tier(client, db_session, test_user, auth_token):
    """Test getting quota info for pro tier user"""
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=750,
        period_start=datetime.utcnow() - timedelta(days=15),
        period_end=datetime.utcnow() + timedelta(days=15),
        next_billing_at=datetime.utcnow() + timedelta(days=15)
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.get_quota_info') as mock_get_quota:
        mock_get_quota.return_value = {
            "tier": "pro",
            "status": "active",
            "quota_used": 750,
            "quota_limit": 1000,
            "remaining": 250,
            "usage_percentage": 75.0,
            "is_unlimited": False,
            "period_start": subscription.period_start.isoformat(),
            "period_end": subscription.period_end.isoformat(),
            "next_billing_at": subscription.next_billing_at.isoformat()
        }
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should work for pro tier
        assert response.status_code != 402


def test_quota_approaching_limit_warning(client, db_session, test_user, auth_token):
    """Test quota warning when approaching limit"""
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="starter",
        status="active",
        monthly_query_quota=100,
        queries_this_period=85  # 85% usage
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
        mock_check_quota.return_value = subscription
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should still work but might log warning
        assert response.status_code != 402


def test_redis_quota_tracker_integration(client, db_session, test_user, auth_token):
    """Test Redis-based quota tracking integration"""
    subscription = Subscription(
        workspace_id=test_user.workspace_id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    with patch('app.middleware.quota_middleware.RedisQuotaTracker') as mock_redis_tracker:
        mock_tracker_instance = Mock()
        mock_tracker_instance.check_quota_redis.return_value = True
        mock_tracker_instance.increment_usage_redis.return_value = 501
        mock_redis_tracker.return_value = mock_tracker_instance
        
        response = client.get(
            "/api/v1/rag/query",
            params={"query": "test query"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should work with Redis tracking
        assert response.status_code != 402

