"""
Integration tests for token budget service with Redis
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.chat import ChatMessage, ChatSession
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
        description="Test workspace for token budget"
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
def test_chat_session(db_session, test_workspace):
    session = ChatSession(
        id="test-session-id",
        workspace_id=test_workspace.id,
        created_at=datetime.utcnow()
    )
    db_session.add(session)
    db_session.commit()
    return session


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


@pytest.mark.asyncio
async def test_token_budget_check_within_limits():
    """Test token budget check when within limits"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = None  # No cached usage
        mock_redis.return_value = mock_redis_client
        
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 5000
        
        service = TokenBudgetService(mock_db)
        
        is_within_budget, budget_info = await service.check_token_budget(
            workspace_id="test-workspace",
            requested_tokens=1000,
            daily_limit=10000,
            monthly_limit=100000
        )
        
        assert is_within_budget == True
        assert budget_info["daily_used"] == 5000
        assert budget_info["daily_remaining"] == 5000
        assert budget_info["monthly_used"] == 5000
        assert budget_info["monthly_remaining"] == 95000
        assert budget_info["within_daily_limit"] == True
        assert budget_info["within_monthly_limit"] == True


@pytest.mark.asyncio
async def test_token_budget_check_exceeded_daily():
    """Test token budget check when daily limit exceeded"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = "9500"  # High daily usage
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 9500
        
        service = TokenBudgetService(mock_db)
        
        is_within_budget, budget_info = await service.check_token_budget(
            workspace_id="test-workspace",
            requested_tokens=1000,
            daily_limit=10000,
            monthly_limit=100000
        )
        
        assert is_within_budget == False
        assert budget_info["daily_used"] == 9500
        assert budget_info["daily_remaining"] == 500
        assert budget_info["within_daily_limit"] == False
        assert budget_info["within_monthly_limit"] == True


@pytest.mark.asyncio
async def test_token_budget_check_exceeded_monthly():
    """Test token budget check when monthly limit exceeded"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = "95000"  # High monthly usage
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 95000
        
        service = TokenBudgetService(mock_db)
        
        is_within_budget, budget_info = await service.check_token_budget(
            workspace_id="test-workspace",
            requested_tokens=1000,
            daily_limit=10000,
            monthly_limit=100000
        )
        
        assert is_within_budget == False
        assert budget_info["monthly_used"] == 95000
        assert budget_info["monthly_remaining"] == 5000
        assert budget_info["within_daily_limit"] == True
        assert budget_info["within_monthly_limit"] == False


@pytest.mark.asyncio
async def test_consume_tokens_success():
    """Test consuming tokens successfully"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.incrby.return_value = 1000
        mock_redis_client.expire.return_value = True
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        service = TokenBudgetService(mock_db)
        
        result = await service.consume_tokens(
            workspace_id="test-workspace",
            tokens_used=1000,
            model_used="gemini-pro"
        )
        
        assert result == True
        # Verify Redis operations were called
        assert mock_redis_client.incrby.call_count == 2  # Daily and monthly
        assert mock_redis_client.expire.call_count == 2


@pytest.mark.asyncio
async def test_consume_tokens_redis_error():
    """Test consuming tokens when Redis fails"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.incrby.side_effect = Exception("Redis connection failed")
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        service = TokenBudgetService(mock_db)
        
        result = await service.consume_tokens(
            workspace_id="test-workspace",
            tokens_used=1000,
            model_used="gemini-pro"
        )
        
        assert result == False


@pytest.mark.asyncio
async def test_get_budget_info():
    """Test getting complete budget information"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = "5000"  # Cached usage
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        service = TokenBudgetService(mock_db)
        
        budget_info = await service.get_budget_info("test-workspace")
        
        assert "daily_used" in budget_info
        assert "monthly_used" in budget_info
        assert "reset_daily_at" in budget_info
        assert "reset_monthly_at" in budget_info
        assert budget_info["daily_used"] == 5000
        assert budget_info["monthly_used"] == 5000


@pytest.mark.asyncio
async def test_reset_budget():
    """Test resetting token budget"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.keys.return_value = [
            "token_budget:test-workspace:daily:2024-01-01",
            "token_budget:test-workspace:monthly:2024-01"
        ]
        mock_redis_client.delete.return_value = 2
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        service = TokenBudgetService(mock_db)
        
        result = await service.reset_budget("test-workspace")
        
        assert result == True
        mock_redis_client.keys.assert_called_once_with("token_budget:test-workspace:*")
        mock_redis_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_daily_usage_redis_fallback():
    """Test getting daily usage with Redis fallback to database"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = None  # No Redis cache
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 3000
        
        service = TokenBudgetService(mock_db)
        
        daily_usage = await service._get_daily_usage("test-workspace")
        
        assert daily_usage == 3000
        # Verify database query was made
        mock_db.query.assert_called_once()


@pytest.mark.asyncio
async def test_get_monthly_usage_redis_fallback():
    """Test getting monthly usage with Redis fallback to database"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url') as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = None  # No Redis cache
        mock_redis.return_value = mock_redis_client
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 25000
        
        service = TokenBudgetService(mock_db)
        
        monthly_usage = await service._get_monthly_usage("test-workspace")
        
        assert monthly_usage == 25000
        # Verify database query was made
        mock_db.query.assert_called_once()


@pytest.mark.asyncio
async def test_token_budget_redis_unavailable():
    """Test token budget service when Redis is unavailable"""
    from app.services.token_budget import TokenBudgetService
    
    with patch('redis.asyncio.aioredis.from_url', side_effect=Exception("Redis unavailable")):
        mock_db = Mock()
        service = TokenBudgetService(mock_db)
        
        # Should initialize without Redis
        assert service.redis_client is None
        
        # Should still work with database fallback
        is_within_budget, budget_info = await service.check_token_budget(
            workspace_id="test-workspace",
            requested_tokens=1000,
            daily_limit=10000,
            monthly_limit=100000
        )
        
        assert is_within_budget == True  # Should fail open


@pytest.mark.asyncio
async def test_consume_tokens_no_redis():
    """Test consuming tokens when Redis is not available"""
    from app.services.token_budget import TokenBudgetService
    
    mock_db = Mock()
    service = TokenBudgetService(mock_db)
    service.redis_client = None  # Simulate no Redis
    
    result = await service.consume_tokens(
        workspace_id="test-workspace",
        tokens_used=1000,
        model_used="gemini-pro"
    )
    
    assert result == True  # Should still succeed


def test_token_budget_endpoint_integration(client, db_session, test_user, test_chat_session, auth_token):
    """Test token budget endpoint integration"""
    # Create chat message with token usage
    chat_message = ChatMessage(
        session_id=test_chat_session.id,
        content="Test message",
        role="user",
        tokens_used=150,
        created_at=datetime.utcnow()
    )
    db_session.add(chat_message)
    db_session.commit()
    
    with patch('app.services.token_budget.TokenBudgetService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_budget_info.return_value = {
            "daily_used": 5000,
            "monthly_used": 25000,
            "reset_daily_at": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
            "reset_monthly_at": (datetime.utcnow() + timedelta(days=15)).isoformat()
        }
        mock_service_class.return_value = mock_service
        
        response = client.get(
            "/api/v1/performance/token-budget",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_used" in data
        assert "monthly_used" in data
        assert data["daily_used"] == 5000
        assert data["monthly_used"] == 25000


def test_reset_token_budget_endpoint_integration(client, db_session, test_user, auth_token):
    """Test reset token budget endpoint integration"""
    with patch('app.services.token_budget.TokenBudgetService') as mock_service_class:
        mock_service = Mock()
        mock_service.reset_budget.return_value = True
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/v1/performance/token-budget/reset",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Token budget reset successfully" in data["message"]


def test_token_budget_endpoint_authentication_required(client):
    """Test token budget endpoint requires authentication"""
    response = client.get("/api/v1/performance/token-budget")
    assert response.status_code == 401


def test_reset_token_budget_endpoint_authentication_required(client):
    """Test reset token budget endpoint requires authentication"""
    response = client.post("/api/v1/performance/token-budget/reset")
    assert response.status_code == 401

