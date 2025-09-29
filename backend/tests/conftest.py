"""
Pytest configuration and fixtures for CustomerCareGPT tests
"""

import pytest
import asyncio
import tempfile
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

# Set testing environment before importing app
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["STRIPE_API_KEY"] = "test-stripe-key"
os.environ["ENVIRONMENT"] = "testing"

from app.main import app
from app.core.database import get_db, Base
# Import all models to ensure relationships are resolved
from app.models import User, Workspace, Document, DocumentChunk, ChatSession, ChatMessage, EmbedCode, Subscription

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

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
def db_session() -> Generator:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_workspace(db_session) -> Workspace:
    """Create a test workspace."""
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        domain="test.example.com"
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)
    return workspace

@pytest.fixture
def test_user(db_session, test_workspace) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",  # "password"
        full_name="Test User",
        workspace_id=test_workspace.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_subscription(db_session, test_workspace) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        workspace_id=test_workspace.id,
        tier="pro",
        status="active",
        monthly_query_quota=100000,
        queries_this_period=0,
        period_start="2024-01-01T00:00:00Z",
        period_end="2024-02-01T00:00:00Z"
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription

@pytest.fixture
def test_document(db_session, test_user) -> Document:
    """Create a test document."""
    document = Document(
        filename="test_document.pdf",
        file_path="/tmp/test_document.pdf",
        file_size=1024,
        file_type="application/pdf",
        status="processed",
        user_id=test_user.id,
        workspace_id=test_user.workspace_id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

@pytest.fixture
def test_chat_session(db_session, test_user) -> ChatSession:
    """Create a test chat session."""
    session = ChatSession(
        user_id=test_user.id,
        workspace_id=test_user.workspace_id,
        user_label="Test Customer"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

@pytest.fixture
def test_embed_code(db_session, test_user) -> EmbedCode:
    """Create a test embed code."""
    embed_code = EmbedCode(
        workspace_id=test_user.workspace_id,
        user_id=test_user.id,
        snippet_template="<script>console.log('test')</script>",
        default_config={"theme": {"primary": "#4f46e5"}},
        client_api_key="test-api-key"
    )
    db_session.add(embed_code)
    db_session.commit()
    db_session.refresh(embed_code)
    return embed_code

@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers for test user."""
    # In a real test, you'd generate a proper JWT token
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service responses."""
    with patch('app.services.gemini_service.GeminiService') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_response.return_value = {
            "answer": "This is a test response from Gemini.",
            "sources": [{"chunk_id": "123", "document_id": "doc1", "chunk_index": 0}],
            "tokens_used": 150,
            "model_used": "gemini-pro"
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_embeddings_service():
    """Mock embeddings service responses."""
    with patch('app.services.embeddings_service.EmbeddingsService') as mock:
        mock_instance = MagicMock()
        mock_instance.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_vector_search_service():
    """Mock vector search service responses."""
    with patch('app.services.vector_search_service.VectorSearchService') as mock:
        mock_instance = MagicMock()
        mock_instance.search.return_value = [
            {"chunk_id": "123", "content": "Test content", "score": 0.9},
            {"chunk_id": "124", "content": "More test content", "score": 0.8}
        ]
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service responses."""
    with patch('app.services.stripe_service.StripeService') as mock:
        mock_instance = MagicMock()
        mock_instance.create_checkout_session.return_value = MagicMock(
            id="cs_test_123",
            url="http://localhost:3000/billing/checkout/test"
        )
        mock_instance.create_billing_portal_session.return_value = MagicMock(
            url="http://localhost:3000/billing/portal/test"
        )
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('app.core.database.redis_client') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        yield mock

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document content for testing purposes.")
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

@pytest.fixture
def test_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"

# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use different DB for tests
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["GEMINI_API_KEY"] = "test-gemini-key"
    os.environ["STRIPE_API_KEY"] = "test-stripe-key"
    os.environ["ENVIRONMENT"] = "testing"
    
    yield
    
    # Cleanup
    for key in ["TESTING", "DATABASE_URL", "REDIS_URL", "SECRET_KEY", "GEMINI_API_KEY", "STRIPE_API_KEY", "ENVIRONMENT"]:
        if key in os.environ:
            del os.environ[key]
