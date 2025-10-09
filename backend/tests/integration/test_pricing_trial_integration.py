"""
Integration tests for pricing and trial management endpoints
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
        description="Test workspace for pricing"
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


def test_get_pricing_plans_success(client):
    """Test getting pricing plans"""
    with patch('app.services.stripe_service.stripe_service') as mock_stripe:
        mock_stripe.plans = {
            'starter': {
                'name': 'Starter Plan',
                'features': ['100 queries/month', '1 document'],
                'price_id': 'price_starter'
            },
            'pro': {
                'name': 'Pro Plan',
                'features': ['1000 queries/month', '10 documents'],
                'price_id': 'price_pro'
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'features': ['Unlimited queries', 'Unlimited documents'],
                'price_id': 'price_enterprise'
            }
        }
        
        response = client.get("/api/v1/pricing/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert data["currency"] == "usd"
        assert data["trial_days"] == 7
        assert len(data["plans"]) == 3
        
        # Check starter plan
        starter_plan = next(p for p in data["plans"] if p["id"] == "starter")
        assert starter_plan["name"] == "Starter Plan"
        assert starter_plan["price"] == 2000  # $20 in cents
        assert starter_plan["popular"] == False
        
        # Check pro plan (should be popular)
        pro_plan = next(p for p in data["plans"] if p["id"] == "pro")
        assert pro_plan["popular"] == True


def test_get_pricing_plans_error(client):
    """Test pricing plans endpoint handles errors"""
    with patch('app.services.stripe_service.stripe_service') as mock_stripe:
        mock_stripe.plans = {}
        
        response = client.get("/api/v1/pricing/plans")
        
        assert response.status_code == 500


def test_start_free_trial_success(client, db_session):
    """Test starting a free trial successfully"""
    with patch('app.services.stripe_service.stripe_service') as mock_stripe:
        mock_stripe.get_plan_config.return_value = {
            'monthly_query_quota': 100
        }
        
        response = client.post(
            "/api/v1/pricing/start-trial",
            json={
                "email": "newuser@example.com",
                "mobile_phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "7-day free trial started" in data["message"]
        assert "trial_end" in data
        
        # Verify subscription was created
        subscription = db_session.query(Subscription).filter(
            Subscription.workspace_id == "newuser@example.com",
            Subscription.tier == "free_trial"
        ).first()
        assert subscription is not None
        assert subscription.status == "trialing"
        assert subscription.monthly_query_quota == 100


def test_start_free_trial_already_exists(client, db_session):
    """Test starting trial when one already exists"""
    # Create existing trial
    existing_trial = Subscription(
        workspace_id="existing@example.com",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=0,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(existing_trial)
    db_session.commit()
    
    response = client.post(
        "/api/v1/pricing/start-trial",
        json={
            "email": "existing@example.com",
            "mobile_phone": "+1234567890"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "already used your free trial" in data["message"]


def test_start_free_trial_duplicate_mobile(client, db_session):
    """Test starting trial with duplicate mobile number"""
    # Create user with existing mobile
    existing_user = User(
        id="existing-user-id",
        email="different@example.com",
        mobile_phone="+1234567890",
        hashed_password="hashed_password"
    )
    db_session.add(existing_user)
    
    existing_trial = Subscription(
        workspace_id="different@example.com",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100
    )
    db_session.add(existing_trial)
    db_session.commit()
    
    response = client.post(
        "/api/v1/pricing/start-trial",
        json={
            "email": "new@example.com",
            "mobile_phone": "+1234567890"  # Same mobile as existing trial
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "already used your free trial" in data["message"]


def test_start_free_trial_active_subscription(client, db_session):
    """Test starting trial when user has active subscription"""
    # Create active subscription
    active_subscription = Subscription(
        workspace_id="active@example.com",
        tier="pro",
        status="active",
        monthly_query_quota=1000
    )
    db_session.add(active_subscription)
    db_session.commit()
    
    response = client.post(
        "/api/v1/pricing/start-trial",
        json={
            "email": "active@example.com",
            "mobile_phone": "+1234567890"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "already have an active subscription" in data["message"]


def test_get_trial_status_active(client, db_session):
    """Test getting trial status for active trial"""
    trial_end = datetime.utcnow() + timedelta(days=3)
    trial_subscription = Subscription(
        workspace_id="trial@example.com",
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=trial_end
    )
    db_session.add(trial_subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/pricing/trial-status",
        params={"workspace_id": "trial@example.com"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_trial"] == True
    assert data["plan"] == "free_trial"
    assert data["days_remaining"] == 3
    assert data["quota_used"] == 25
    assert data["quota_limit"] == 100


def test_get_trial_status_expired(client, db_session):
    """Test getting trial status for expired trial"""
    trial_end = datetime.utcnow() - timedelta(days=1)
    trial_subscription = Subscription(
        workspace_id="expired@example.com",
        tier="free_trial",
        status="expired",
        monthly_query_quota=100,
        period_end=trial_end
    )
    db_session.add(trial_subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/pricing/trial-status",
        params={"workspace_id": "expired@example.com"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_trial"] == True
    assert data["plan"] == "free_trial"
    assert data["days_remaining"] == 0


def test_get_trial_status_no_trial(client, db_session):
    """Test getting trial status when no trial exists"""
    response = client.get(
        "/api/v1/pricing/trial-status",
        params={"workspace_id": "notrial@example.com"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_trial"] == False
    assert "No active trial found" in data["message"]


def test_get_white_label_pricing(client):
    """Test getting white label pricing"""
    with patch('app.services.stripe_service.stripe_service') as mock_stripe:
        mock_stripe.get_plan_config.return_value = {
            'name': 'White Label License',
            'features': ['Complete white-label solution', 'Custom branding'],
            'price_id': 'price_white_label'
        }
        
        response = client.get("/api/v1/pricing/white-label")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "white_label"
        assert data["name"] == "White Label License"
        assert data["price"] == 99900  # $999 in cents
        assert data["currency"] == "usd"
        assert data["interval"] == "one_time"
        assert data["popular"] == False


def test_start_trial_validation_error(client):
    """Test trial start with validation errors"""
    with patch('app.services.auth.AuthService') as mock_auth:
        mock_auth_instance = Mock()
        mock_auth_instance.validate_user_registration.return_value = {
            "valid": False,
            "message": "Invalid email format"
        }
        mock_auth.return_value = mock_auth_instance
        
        response = client.post(
            "/api/v1/pricing/start-trial",
            json={
                "email": "invalid-email",
                "mobile_phone": "invalid-phone"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "Invalid email format" in data["message"]


def test_start_trial_database_error(client, db_session):
    """Test trial start handles database errors"""
    with patch('app.services.stripe_service.stripe_service') as mock_stripe:
        mock_stripe.get_plan_config.return_value = {
            'monthly_query_quota': 100
        }
        
        # Mock database error
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            response = client.post(
                "/api/v1/pricing/start-trial",
                json={
                    "email": "error@example.com",
                    "mobile_phone": "+1234567890"
                }
            )
            
            assert response.status_code == 500

