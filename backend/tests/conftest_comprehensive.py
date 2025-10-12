"""
Comprehensive pytest configuration and fixtures for CustomerCareGPT
Enhanced fixtures for comprehensive testing
"""

import pytest
import asyncio
import tempfile
import os
import sys
from typing import Generator, AsyncGenerator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set testing environment before importing app
os.environ.update({
    "TESTING": "true",
    "DATABASE_URL": "sqlite:///:memory:",
    "REDIS_URL": "redis://localhost:6379/1",
    "SECRET_KEY": "test-secret-key-change-in-production",
    "JWT_SECRET": "test-jwt-secret-change-in-production",
    "GEMINI_API_KEY": "test-gemini-key",
    "STRIPE_API_KEY": "test-stripe-key",
    "ENVIRONMENT": "testing",
    "DEBUG": "true",
    "LOG_LEVEL": "DEBUG",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "ENABLE_RATE_LIMITING": "false",  # Disable for testing
    "ENABLE_INPUT_VALIDATION": "true",
    "ENABLE_SECURITY_HEADERS": "true",
    "ENABLE_REQUEST_LOGGING": "false",  # Disable for testing
    "PROMETHEUS_ENABLED": "false",  # Disable for testing
    "SENTRY_DSN": "",  # Disable for testing
})

from app.main import app
from app.core.database import get_db, Base
from app.models import (
    User, Workspace, Document, DocumentChunk, ChatSession, 
    ChatMessage, EmbedCode, Subscription, TeamMember, Performance
)

# Test database configuration - use in-memory SQLite for speed
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_workspace(test_db):
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        description="Test workspace for testing"
    )
    test_db.add(workspace)
    test_db.commit()
    test_db.refresh(workspace)
    return workspace


@pytest.fixture(scope="function")
def test_user(test_db, test_workspace):
    """Create a test user."""
    from app.utils.password import PasswordValidator
    
    password_validator = PasswordValidator()
    hashed_password = password_validator.hash_password("test_password_123")
    
    user = User(
        email="test@example.com",
        hashed_password=hashed_password,
        mobile_phone="+1234567890",
        full_name="Test User",
        workspace_id=test_workspace.id,
        is_verified=True,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_2(test_db, test_workspace):
    """Create a second test user."""
    from app.utils.password import PasswordValidator
    
    password_validator = PasswordValidator()
    hashed_password = password_validator.hash_password("test_password_456")
    
    user = User(
        email="test2@example.com",
        hashed_password=hashed_password,
        mobile_phone="+1234567891",
        full_name="Test User 2",
        workspace_id=test_workspace.id,
        is_verified=True,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user, client):
    """Create authentication headers for test user."""
    # Login to get token
    login_data = {
        "identifier": test_user.email,
        "password": "test_password_123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        # Fallback: create token manually for testing
        from app.services.auth import AuthService
        auth_service = AuthService()
        token = auth_service.create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_document(test_db, test_user, test_workspace):
    """Create a test document."""
    document = Document(
        filename="test_document.pdf",
        content_type="application/pdf",
        size=1024,
        status="done",
        workspace_id=test_workspace.id,
        uploaded_by=test_user.id,
        title="Test Document",
        description="A test document for testing purposes"
    )
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    return document


@pytest.fixture(scope="function")
def test_document_chunks(test_db, test_document):
    """Create test document chunks."""
    chunks = [
        DocumentChunk(
            document_id=test_document.id,
            text="This is the first chunk of the test document.",
            chunk_index=0,
            chunk_metadata={"page": 1, "section": "introduction"}
        ),
        DocumentChunk(
            document_id=test_document.id,
            text="This is the second chunk of the test document.",
            chunk_index=1,
            chunk_metadata={"page": 1, "section": "main_content"}
        ),
        DocumentChunk(
            document_id=test_document.id,
            text="This is the third chunk of the test document.",
            chunk_index=2,
            chunk_metadata={"page": 2, "section": "conclusion"}
        )
    ]
    
    for chunk in chunks:
        test_db.add(chunk)
    test_db.commit()
    
    for chunk in chunks:
        test_db.refresh(chunk)
    
    return chunks


@pytest.fixture(scope="function")
def test_chat_session(test_db, test_user, test_workspace):
    """Create a test chat session."""
    session = ChatSession(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        visitor_ip="127.0.0.1",
        user_agent="Mozilla/5.0 (Test Browser)",
        referrer="https://example.com",
        user_label="Test User"
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture(scope="function")
def test_chat_messages(test_db, test_chat_session):
    """Create test chat messages."""
    messages = [
        ChatMessage(
            session_id=test_chat_session.id,
            message_type="user",
            content="Hello, I need help with my account.",
            model_used="gpt-3.5-turbo",
            response_time_ms=1500,
            tokens_used=25,
            confidence_score="high"
        ),
        ChatMessage(
            session_id=test_chat_session.id,
            message_type="assistant",
            content="Hello! I'd be happy to help you with your account. What specific issue are you experiencing?",
            model_used="gpt-3.5-turbo",
            response_time_ms=2000,
            tokens_used=35,
            confidence_score="high",
            sources_used=["doc1", "doc2"]
        )
    ]
    
    for message in messages:
        test_db.add(message)
    test_db.commit()
    
    for message in messages:
        test_db.refresh(message)
    
    return messages


@pytest.fixture(scope="function")
def test_embed_code(test_db, test_user, test_workspace):
    """Create a test embed code."""
    embed_code = EmbedCode(
        workspace_id=test_workspace.id,
        created_by=test_user.id,
        title="Test Widget",
        primary_color="#007bff",
        secondary_color="#f8f9fa",
        text_color="#111111",
        position="bottom-right",
        welcome_message="Hello! How can I help you?",
        client_api_key="test_api_key_123",
        is_active=True
    )
    test_db.add(embed_code)
    test_db.commit()
    test_db.refresh(embed_code)
    return embed_code


@pytest.fixture(scope="function")
def test_subscription(test_db, test_workspace):
    """Create a test subscription."""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        plan_name="starter",
        status="active",
        current_period_start="2024-01-01T00:00:00Z",
        current_period_end="2024-02-01T00:00:00Z",
        stripe_subscription_id="sub_test_123",
        stripe_customer_id="cus_test_123"
    )
    test_db.add(subscription)
    test_db.commit()
    test_db.refresh(subscription)
    return subscription


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for testing."""
    with patch('app.core.database.redis_manager') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.exists.return_value = False
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        yield mock_redis


@pytest.fixture(scope="function")
def mock_gemini():
    """Mock Gemini service for testing."""
    with patch('app.services.gemini_service.GeminiService') as mock_gemini:
        mock_instance = MagicMock()
        mock_instance.generate_response.return_value = {
            "message": "This is a test response from Gemini.",
            "sources": ["doc1", "doc2"],
            "confidence": "high"
        }
        mock_gemini.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_vector_service():
    """Mock vector service for testing."""
    with patch('app.services.vector_service.VectorService') as mock_vector:
        mock_instance = MagicMock()
        mock_instance.search_similar_chunks.return_value = [
            {
                "text": "This is a test document chunk.",
                "metadata": {"document_id": "doc1", "chunk_index": 0},
                "distance": 0.1
            }
        ]
        mock_instance.add_document_chunks.return_value = True
        mock_vector.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_document_service():
    """Mock document service for testing."""
    with patch('app.services.document_service.DocumentService') as mock_doc:
        mock_instance = MagicMock()
        mock_instance.process_document.return_value = {
            "job_id": "test_job_123",
            "status": "queued"
        }
        mock_instance.get_job_status.return_value = {
            "job_id": "test_job_123",
            "status": "finished",
            "result": {"document_id": "doc_123"},
            "progress": 100
        }
        mock_doc.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_file_processing():
    """Mock file processing for testing."""
    with patch('app.utils.file_processing.extract_text_from_file') as mock_extract:
        mock_extract.return_value = "This is extracted text from a test document."
        yield mock_extract


@pytest.fixture(scope="function")
def mock_embeddings():
    """Mock embeddings service for testing."""
    with patch('app.services.embeddings_service.EmbeddingsService') as mock_embeddings:
        mock_instance = MagicMock()
        mock_instance.generate_embedding.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_stripe():
    """Mock Stripe service for testing."""
    with patch('app.services.billing_service.stripe') as mock_stripe:
        mock_stripe.Customer.create.return_value = {"id": "cus_test_123"}
        mock_stripe.Subscription.create.return_value = {"id": "sub_test_123"}
        mock_stripe.Price.list.return_value = {"data": []}
        yield mock_stripe


@pytest.fixture(scope="function")
def mock_email():
    """Mock email service for testing."""
    with patch('app.services.email_service.EmailService') as mock_email:
        mock_instance = MagicMock()
        mock_instance.send_email.return_value = True
        mock_email.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_analytics():
    """Mock analytics service for testing."""
    with patch('app.services.analytics_service.AnalyticsService') as mock_analytics:
        mock_instance = MagicMock()
        mock_instance.track_event.return_value = True
        mock_instance.get_overview.return_value = {
            "total_documents": 10,
            "total_messages": 100,
            "active_sessions": 5
        }
        mock_analytics.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(b"Test PDF content")
        tmp_file.flush()
        yield tmp_file.name
    os.unlink(tmp_file.name)


@pytest.fixture(scope="function")
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"


@pytest.fixture(scope="function")
def sample_docx_content():
    """Sample DOCX content for testing."""
    return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"


@pytest.fixture(scope="function")
def sample_txt_content():
    """Sample TXT content for testing."""
    return b"This is a test document with some content for processing and analysis."


@pytest.fixture(scope="function")
def mock_health_check():
    """Mock health check for testing."""
    with patch('app.utils.health.HealthChecker') as mock_health:
        mock_instance = MagicMock()
        mock_instance.run_all_checks.return_value = {
            "database": {"status": "healthy", "response_time": 10},
            "redis": {"status": "healthy", "response_time": 5},
            "chromadb": {"status": "healthy", "response_time": 15},
            "overall": True
        }
        mock_health.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_metrics():
    """Mock metrics collection for testing."""
    with patch('app.utils.metrics.metrics_collector') as mock_metrics:
        mock_metrics.increment_request_count.return_value = None
        mock_metrics.record_response_time.return_value = None
        mock_metrics.increment_error_count.return_value = None
        mock_metrics.set_database_connections.return_value = None
        yield mock_metrics


@pytest.fixture(scope="function")
def mock_logger():
    """Mock structured logger for testing."""
    with patch('app.utils.logging_config.logger') as mock_logger:
        mock_logger.info.return_value = None
        mock_logger.error.return_value = None
        mock_logger.warning.return_value = None
        mock_logger.debug.return_value = None
        yield mock_logger


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "system: mark test as a system test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "documents: mark test as document processing related"
    )
    config.addinivalue_line(
        "markers", "chat: mark test as chat functionality related"
    )
    config.addinivalue_line(
        "markers", "rag: mark test as RAG system related"
    )
    config.addinivalue_line(
        "markers", "billing: mark test as billing related"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security related"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance related"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add markers based on test name
        if "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth)
        elif "document" in item.name.lower():
            item.add_marker(pytest.mark.documents)
        elif "chat" in item.name.lower():
            item.add_marker(pytest.mark.chat)
        elif "rag" in item.name.lower():
            item.add_marker(pytest.mark.rag)
        elif "billing" in item.name.lower():
            item.add_marker(pytest.mark.billing)
        elif "security" in item.name.lower():
            item.add_marker(pytest.mark.security)
        elif "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker for tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["concurrent", "load", "stress", "large"]):
            item.add_marker(pytest.mark.slow)
