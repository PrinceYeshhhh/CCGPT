"""
Integration tests for vector search endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

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
        description="Test workspace for vector search"
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
def test_subscription(db_session, test_workspace):
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="active",
        monthly_query_quota=1000,
        queries_this_period=0
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


def test_vector_search_post_success(client, db_session, test_user, test_subscription, auth_token):
    """Test vector search via POST endpoint"""
    with patch('app.services.vector_service.VectorService') as mock_vector_service:
        mock_service_instance = Mock()
        mock_service_instance.vector_search.return_value = [
            {
                "id": "doc1",
                "content": "Test document content",
                "score": 0.95,
                "metadata": {"source": "test.pdf"}
            }
        ]
        mock_vector_service.return_value = mock_service_instance
        
        response = client.post(
            "/api/v1/vector/search",
            json={
                "query": "test query",
                "top_k": 5
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["total_results"] == 1
        assert data["results"][0]["content"] == "Test document content"


def test_vector_search_get_success(client, db_session, test_user, test_subscription, auth_token):
    """Test vector search via GET endpoint"""
    with patch('app.services.vector_service.VectorService') as mock_vector_service:
        mock_service_instance = Mock()
        mock_service_instance.vector_search.return_value = [
            {
                "id": "doc1",
                "content": "Test document content",
                "score": 0.95,
                "metadata": {"source": "test.pdf"}
            }
        ]
        mock_vector_service.return_value = mock_service_instance
        
        response = client.get(
            "/api/v1/vector/search",
            params={"query": "test query", "top_k": 5},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1


def test_vector_search_authentication_required(client):
    """Test vector search requires authentication"""
    response = client.post(
        "/api/v1/vector/search",
        json={"query": "test query", "top_k": 5}
    )
    assert response.status_code == 401


def test_vector_search_invalid_top_k(client, auth_token):
    """Test vector search with invalid top_k parameter"""
    response = client.get(
        "/api/v1/vector/search",
        params={"query": "test query", "top_k": 100},  # Exceeds max limit
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422


def test_clear_vector_cache_success(client, db_session, test_user, test_subscription, auth_token):
    """Test clearing vector search cache"""
    with patch('app.services.vector_search_service.vector_search_service') as mock_service:
        mock_service.clear_cache.return_value = True
        
        response = client.delete(
            "/api/v1/vector/cache",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache cleared successfully"


def test_clear_vector_cache_failure(client, db_session, test_user, test_subscription, auth_token):
    """Test clearing vector search cache failure"""
    with patch('app.services.vector_search_service.vector_search_service') as mock_service:
        mock_service.clear_cache.return_value = False
        
        response = client.delete(
            "/api/v1/vector/cache",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500


def test_get_vector_stats_success(client, db_session, test_user, test_subscription, auth_token):
    """Test getting vector search statistics"""
    with patch('app.services.vector_service.VectorService') as mock_vector_service, \
         patch('app.services.vector_search_service.vector_search_service') as mock_search_service, \
         patch('app.services.embeddings_service.embeddings_service') as mock_embeddings_service:
        
        mock_vector_service.return_value.get_collection_stats.return_value = {
            "total_documents": 100,
            "total_chunks": 500
        }
        mock_search_service.get_cache_stats.return_value = {
            "cache_hits": 50,
            "cache_misses": 10
        }
        mock_embeddings_service.get_embedding_stats.return_value = {
            "total_embeddings": 500,
            "model_name": "all-mpnet-base-v2"
        }
        
        response = client.get(
            "/api/v1/vector/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "collection" in data
        assert "cache" in data
        assert "embeddings" in data


def test_vector_search_service_error(client, db_session, test_user, test_subscription, auth_token):
    """Test vector search handles service errors gracefully"""
    with patch('app.services.vector_service.VectorService') as mock_vector_service:
        mock_service_instance = Mock()
        mock_service_instance.vector_search.side_effect = Exception("Vector service error")
        mock_vector_service.return_value = mock_service_instance
        
        response = client.post(
            "/api/v1/vector/search",
            json={"query": "test query", "top_k": 5},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Vector search failed" in data["detail"]


def test_vector_search_empty_results(client, db_session, test_user, test_subscription, auth_token):
    """Test vector search with no results"""
    with patch('app.services.vector_service.VectorService') as mock_vector_service:
        mock_service_instance = Mock()
        mock_service_instance.vector_search.return_value = []
        mock_vector_service.return_value = mock_service_instance
        
        response = client.post(
            "/api/v1/vector/search",
            json={"query": "nonexistent query", "top_k": 5},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "nonexistent query"
        assert data["results"] == []
        assert data["total_results"] == 0

