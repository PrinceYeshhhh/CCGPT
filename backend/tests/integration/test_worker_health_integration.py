"""
Integration tests for worker health monitoring endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
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
        description="Test workspace for worker health"
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


def test_get_worker_health_success(client, db_session, test_user, auth_token):
    """Test getting worker health status successfully"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "healthy",
            "workers": {
                "document_processor": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 150,
                    "failed_jobs": 2,
                    "queue_size": 5
                },
                "embedding_worker": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 300,
                    "failed_jobs": 1,
                    "queue_size": 2
                }
            },
            "system": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 23.1,
                "uptime": "2d 5h 30m"
            }
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "workers" in data
        assert "system" in data
        assert "document_processor" in data["workers"]
        assert "embedding_worker" in data["workers"]


def test_get_worker_health_degraded(client, db_session, test_user, auth_token):
    """Test getting worker health status when degraded"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "degraded",
            "workers": {
                "document_processor": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 150,
                    "failed_jobs": 2,
                    "queue_size": 5
                },
                "embedding_worker": {
                    "status": "error",
                    "last_heartbeat": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                    "processed_jobs": 300,
                    "failed_jobs": 15,
                    "queue_size": 50,
                    "error": "Connection timeout to vector database"
                }
            },
            "system": {
                "cpu_usage": 85.2,
                "memory_usage": 92.1,
                "disk_usage": 45.3,
                "uptime": "2d 5h 30m"
            },
            "alerts": [
                "Embedding worker is not responding",
                "High memory usage detected",
                "Queue size is growing rapidly"
            ]
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["workers"]["embedding_worker"]["status"] == "error"
        assert "alerts" in data
        assert len(data["alerts"]) == 3


def test_get_worker_health_unhealthy(client, db_session, test_user, auth_token):
    """Test getting worker health status when unhealthy"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "unhealthy",
            "workers": {
                "document_processor": {
                    "status": "stopped",
                    "last_heartbeat": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "processed_jobs": 150,
                    "failed_jobs": 25,
                    "queue_size": 100,
                    "error": "Worker process crashed"
                },
                "embedding_worker": {
                    "status": "stopped",
                    "last_heartbeat": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "processed_jobs": 300,
                    "failed_jobs": 50,
                    "queue_size": 200,
                    "error": "Out of memory"
                }
            },
            "system": {
                "cpu_usage": 95.8,
                "memory_usage": 98.5,
                "disk_usage": 89.2,
                "uptime": "2d 5h 30m"
            },
            "alerts": [
                "All workers are down",
                "Critical: System resources exhausted",
                "Document processing queue is backing up"
            ]
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["workers"]["document_processor"]["status"] == "stopped"
        assert data["workers"]["embedding_worker"]["status"] == "stopped"
        assert "alerts" in data


def test_get_worker_health_authentication_required(client):
    """Test worker health requires authentication"""
    response = client.get("/api/v1/workers/health")
    assert response.status_code == 401


def test_get_worker_health_service_error(client, db_session, test_user, auth_token):
    """Test worker health handles service errors"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.side_effect = Exception("Worker health service unavailable")
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500


def test_get_worker_health_no_workers(client, db_session, test_user, auth_token):
    """Test worker health when no workers are running"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "unhealthy",
            "workers": {},
            "system": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "uptime": "0s"
            },
            "alerts": [
                "No workers detected",
                "System may not be properly configured"
            ]
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["workers"] == {}
        assert "No workers detected" in data["alerts"]


def test_get_worker_health_partial_failure(client, db_session, test_user, auth_token):
    """Test worker health when some workers are failing"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "degraded",
            "workers": {
                "document_processor": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 150,
                    "failed_jobs": 2,
                    "queue_size": 5
                },
                "embedding_worker": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 300,
                    "failed_jobs": 1,
                    "queue_size": 2
                },
                "notification_worker": {
                    "status": "error",
                    "last_heartbeat": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "processed_jobs": 50,
                    "failed_jobs": 10,
                    "queue_size": 20,
                    "error": "Email service connection failed"
                }
            },
            "system": {
                "cpu_usage": 60.5,
                "memory_usage": 75.2,
                "disk_usage": 30.1,
                "uptime": "1d 12h 45m"
            },
            "alerts": [
                "Notification worker is experiencing issues"
            ]
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["workers"]["document_processor"]["status"] == "running"
        assert data["workers"]["embedding_worker"]["status"] == "running"
        assert data["workers"]["notification_worker"]["status"] == "error"


def test_get_worker_health_high_load(client, db_session, test_user, auth_token):
    """Test worker health under high load conditions"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "degraded",
            "workers": {
                "document_processor": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 1500,
                    "failed_jobs": 5,
                    "queue_size": 150
                },
                "embedding_worker": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 3000,
                    "failed_jobs": 3,
                    "queue_size": 200
                }
            },
            "system": {
                "cpu_usage": 88.5,
                "memory_usage": 85.2,
                "disk_usage": 45.8,
                "uptime": "3d 2h 15m"
            },
            "alerts": [
                "High CPU usage detected",
                "Large queue sizes indicate system overload",
                "Consider scaling up workers"
            ]
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["system"]["cpu_usage"] == 88.5
        assert data["workers"]["document_processor"]["queue_size"] == 150
        assert "High CPU usage detected" in data["alerts"]


def test_get_worker_health_recovery(client, db_session, test_user, auth_token):
    """Test worker health recovery after issues"""
    with patch('app.api.api_v1.endpoints.worker_health.get_worker_health') as mock_health:
        mock_health.return_value = {
            "status": "healthy",
            "workers": {
                "document_processor": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 2000,
                    "failed_jobs": 8,
                    "queue_size": 0
                },
                "embedding_worker": {
                    "status": "running",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_jobs": 4000,
                    "failed_jobs": 5,
                    "queue_size": 0
                }
            },
            "system": {
                "cpu_usage": 45.2,
                "memory_usage": 60.8,
                "disk_usage": 25.1,
                "uptime": "3d 2h 15m"
            },
            "recovery_info": {
                "last_incident": "2h ago",
                "recovery_time": "15 minutes",
                "actions_taken": [
                    "Restarted failed workers",
                    "Cleared stuck queues",
                    "Optimized resource allocation"
                ]
            }
        }
        
        response = client.get(
            "/api/v1/workers/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["workers"]["document_processor"]["queue_size"] == 0
        assert data["workers"]["embedding_worker"]["queue_size"] == 0
        assert "recovery_info" in data
        assert data["recovery_info"]["last_incident"] == "2h ago"

