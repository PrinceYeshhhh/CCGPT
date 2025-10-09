"""
Integration tests for widget status and health check endpoints
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
from app.models.embed import EmbedCode
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
        description="Test workspace for widget status"
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


def test_get_widget_subscription_status_active(client, db_session, test_workspace):
    """Test getting widget subscription status for active subscription"""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/subscription-status",
        params={"workspace_id": test_workspace.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "pro"
    assert data["status"] == "active"
    assert data["is_trial"] == False
    assert data["trial_end"] is None
    assert "Widget is active" in data["message"]


def test_get_widget_subscription_status_trial(client, db_session, test_workspace):
    """Test getting widget subscription status for trial subscription"""
    trial_end = datetime.utcnow() + timedelta(days=3)
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        queries_this_period=25,
        period_end=trial_end
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/subscription-status",
        params={"workspace_id": test_workspace.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "free_trial"
    assert data["status"] == "trialing"
    assert data["is_trial"] == True
    assert data["trial_end"] == trial_end.isoformat()
    assert "Widget is active" in data["message"]


def test_get_widget_subscription_status_inactive(client, db_session, test_workspace):
    """Test getting widget subscription status for inactive subscription"""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="cancelled",
        monthly_query_quota=1000,
        queries_this_period=500
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/subscription-status",
        params={"workspace_id": test_workspace.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert "No active subscription found" in data["message"]


def test_get_widget_subscription_status_no_subscription(client, db_session, test_workspace):
    """Test getting widget subscription status when no subscription exists"""
    response = client.get(
        "/api/v1/widget/subscription-status",
        params={"workspace_id": test_workspace.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert "No active subscription found" in data["message"]


def test_get_embed_widget_status_active(client, db_session, test_workspace):
    """Test getting embed widget status for active widget"""
    # Create active subscription
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="active",
        monthly_query_quota=1000
    )
    db_session.add(subscription)
    
    # Create active embed code
    embed_code = EmbedCode(
        id="test-embed-id",
        workspace_id=test_workspace.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/test-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "pro"
    assert data["status"] == "active"
    assert data["embed_id"] == "test-embed-id"
    assert "Widget is active" in data["message"]


def test_get_embed_widget_status_inactive_embed(client, db_session, test_workspace):
    """Test getting embed widget status for inactive embed code"""
    # Create active subscription
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="active",
        monthly_query_quota=1000
    )
    db_session.add(subscription)
    
    # Create inactive embed code
    embed_code = EmbedCode(
        id="inactive-embed-id",
        workspace_id=test_workspace.id,
        is_active=False,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/inactive-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert "Embed code not found or inactive" in data["message"]


def test_get_embed_widget_status_not_found(client, db_session):
    """Test getting embed widget status for non-existent embed code"""
    response = client.get(
        "/api/v1/widget/embed-status/nonexistent-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert "Embed code not found or inactive" in data["message"]


def test_get_embed_widget_status_no_subscription(client, db_session, test_workspace):
    """Test getting embed widget status when no subscription exists"""
    # Create active embed code but no subscription
    embed_code = EmbedCode(
        id="no-sub-embed-id",
        workspace_id=test_workspace.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/no-sub-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert "No active subscription for this workspace" in data["message"]


def test_get_embed_widget_status_trial(client, db_session, test_workspace):
    """Test getting embed widget status for trial subscription"""
    # Create trial subscription
    trial_end = datetime.utcnow() + timedelta(days=2)
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="free_trial",
        status="trialing",
        monthly_query_quota=100,
        period_end=trial_end
    )
    db_session.add(subscription)
    
    # Create active embed code
    embed_code = EmbedCode(
        id="trial-embed-id",
        workspace_id=test_workspace.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/trial-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "free_trial"
    assert data["status"] == "trialing"
    assert data["is_trial"] == True
    assert data["trial_end"] == trial_end.isoformat()


def test_get_embed_widget_status_expired_trial(client, db_session, test_workspace):
    """Test getting embed widget status for expired trial"""
    # Create expired trial subscription
    trial_end = datetime.utcnow() - timedelta(days=1)
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="free_trial",
        status="expired",
        monthly_query_quota=100,
        period_end=trial_end
    )
    db_session.add(subscription)
    
    # Create active embed code
    embed_code = EmbedCode(
        id="expired-trial-embed-id",
        workspace_id=test_workspace.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/expired-trial-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert "No active subscription for this workspace" in data["message"]


def test_widget_status_database_error(client, db_session, test_workspace):
    """Test widget status handles database errors gracefully"""
    with patch.object(db_session, 'query', side_effect=Exception("Database error")):
        response = client.get(
            "/api/v1/widget/subscription-status",
            params={"workspace_id": test_workspace.id}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to check widget subscription status" in data["detail"]


def test_embed_status_database_error(client, db_session):
    """Test embed status handles database errors gracefully"""
    with patch.object(db_session, 'query', side_effect=Exception("Database error")):
        response = client.get(
            "/api/v1/widget/embed-status/test-embed-id"
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to check embed widget status" in data["detail"]


def test_widget_status_enterprise_tier(client, db_session, test_workspace):
    """Test widget status for enterprise tier subscription"""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="enterprise",
        status="active",
        monthly_query_quota=None,  # Unlimited
        queries_this_period=5000
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/subscription-status",
        params={"workspace_id": test_workspace.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "enterprise"
    assert data["status"] == "active"
    assert data["is_trial"] == False


def test_embed_status_enterprise_tier(client, db_session, test_workspace):
    """Test embed status for enterprise tier subscription"""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="enterprise",
        status="active",
        monthly_query_quota=None
    )
    db_session.add(subscription)
    
    embed_code = EmbedCode(
        id="enterprise-embed-id",
        workspace_id=test_workspace.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(embed_code)
    db_session.commit()
    
    response = client.get(
        "/api/v1/widget/embed-status/enterprise-embed-id"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True
    assert data["plan"] == "enterprise"
    assert data["status"] == "active"

