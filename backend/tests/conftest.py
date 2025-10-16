"""
Pytest configuration and fixtures for CustomerCareGPT tests
"""

import pytest
import asyncio
import tempfile
import os
import sys
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
import builtins as _builtins
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set testing environment before importing app
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["STRIPE_API_KEY"] = "test-stripe-key"
os.environ["ENVIRONMENT"] = "testing"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"  # Longer expiration for tests
os.environ["ENABLE_RATE_LIMITING"] = "false"
os.environ["ENABLE_INPUT_VALIDATION"] = "false"
os.environ["ENABLE_REQUEST_LOGGING"] = "false"
os.environ["PROMETHEUS_ENABLED"] = "false"
os.environ["METRICS_ENABLED"] = "false"
os.environ["HEALTH_CHECK_ENABLED"] = "false"

# Mock Redis to prevent connection issues in tests
import redis
from unittest.mock import MagicMock

# Create a mock Redis client
mock_redis = MagicMock()
mock_redis.ping.return_value = True
mock_redis.get.return_value = None
mock_redis.set.return_value = True
mock_redis.delete.return_value = 1
mock_redis.exists.return_value = False
mock_redis.expire.return_value = True
mock_redis.hget.return_value = None
mock_redis.hset.return_value = 1
mock_redis.hdel.return_value = 1
mock_redis.hgetall.return_value = {}
mock_redis.lpush.return_value = 1
mock_redis.lpop.return_value = None
mock_redis.llen.return_value = 0
mock_redis.lrange.return_value = []
mock_redis.sadd.return_value = 1
mock_redis.srem.return_value = 1
mock_redis.smembers.return_value = set()
mock_redis.scard.return_value = 0
mock_redis.zadd.return_value = 1
mock_redis.zrange.return_value = []
mock_redis.zrem.return_value = 1
mock_redis.zcard.return_value = 0

from app.main import app
from app.core.database import get_db, Base
# Import all models to ensure relationships are resolved
from app.models import User, Workspace, Document, DocumentChunk, ChatSession, ChatMessage, EmbedCode, Subscription

# Test database configuration - use in-memory SQLite for speed
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,  # Disable SQL logging in tests
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Shared session holder so global TestClient and fixtures use the same session
_SHARED_TEST_SESSION = None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables once per session."""
    try:
        # Ensure all models are imported before creating tables
        from app.models import User, Workspace, Document, DocumentChunk, ChatSession, ChatMessage, EmbedCode, Subscription
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception:
            pass  # Ignore cleanup errors

@pytest.fixture(scope="function", autouse=True)
def mock_redis_connections():
    """Mock Redis connections to prevent hanging in tests."""
    with patch('redis.Redis', return_value=mock_redis):
        with patch('redis.from_url', return_value=mock_redis):
            yield

@pytest.fixture(scope="function", autouse=True)
def mock_chromadb():
    """Mock ChromaDB to prevent model loading delays in tests."""
    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.add.return_value = None
    mock_collection.query.return_value = {"documents": [], "metadatas": [], "distances": []}
    mock_collection.delete.return_value = None
    mock_collection.count.return_value = 0
    mock_chroma_client.get_collection.return_value = mock_collection
    mock_chroma_client.create_collection.return_value = mock_collection
    mock_chroma_client.list_collections.return_value = []
    
    with patch('chromadb.Client', return_value=mock_chroma_client):
        with patch('chromadb.PersistentClient', return_value=mock_chroma_client):
            yield

@pytest.fixture(scope="function", autouse=True)
def mock_sentence_transformer():
    """Mock SentenceTransformer to prevent model loading delays in tests."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1] * 384]  # Return fake embeddings
    mock_model.get_sentence_embedding_dimension.return_value = 384
    
    with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
        yield

@pytest.fixture(scope="function", autouse=True)
def mock_chromadb_telemetry():
    """Mock ChromaDB telemetry to prevent errors in tests."""
    with patch('chromadb.telemetry.product.posthog.Posthog.capture', return_value=None):
        yield

@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a fresh database session for each test."""
    # Create session
    global _SHARED_TEST_SESSION
    session = TestingSessionLocal()
    _SHARED_TEST_SESSION = session
    
    try:
        # Ensure tables exist and clear data for isolation per test
        Base.metadata.create_all(bind=engine)
        # Truncate all tables to avoid UNIQUE conflicts across tests (StaticPool keeps memory DB alive)
        try:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        except Exception:
            session.rollback()
        # Rebind global client to this test's DB session so requests share the same session
        try:
            from app.core.database import get_db as _get_db_dep
            def _override_get_db_per_test():
                try:
                    yield session
                finally:
                    pass
            app.dependency_overrides[_get_db_dep] = _override_get_db_per_test
            # Recreate global client bound to this session
            _builtins.client = TestClient(app)  # type: ignore[attr-defined]
        except Exception:
            pass
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client with database dependency override."""
    def override_get_db():
        # Always yield the shared session for this test function
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        # Expose globally for tests that import `client`
        try:
            _builtins.client = test_client  # type: ignore[attr-defined]
        except Exception:
            pass
        yield test_client
    
    app.dependency_overrides.clear()

# Expose a global client variable for tests that import it directly
try:
    if app is not None:
        # Ensure DB dependency override uses the shared session when available
        def _override_get_db():
            try:
                if _SHARED_TEST_SESSION is not None:
                    yield _SHARED_TEST_SESSION
                else:
                    # Fallback to a fresh session (should be rare)
                    _fallback = TestingSessionLocal()
                    try:
                        yield _fallback
                    finally:
                        _fallback.close()
            finally:
                pass
        try:
            # Ensure tables exist before creating the global client
            try:
                Base.metadata.create_all(bind=engine)
            except Exception:
                pass
            app.dependency_overrides[get_db] = _override_get_db
        except Exception:
            pass
        client = TestClient(app)  # type: ignore
        # Also inject into builtins so bare name resolution works in tests
        _builtins.client = client  # type: ignore[attr-defined]
except Exception:
    client = None  # type: ignore

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app  # type: ignore
except Exception:
    app = None

@pytest.fixture
def client():
    if app is None:
        raise RuntimeError("FastAPI app not available for TestClient")
    return TestClient(app)

@pytest.fixture
def test_workspace(db_session) -> Workspace:
    """Create a test workspace."""
    import uuid as _uuid
    workspace = Workspace(
        id=str(_uuid.uuid4()),
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
        is_active=True,
        mobile_phone="+1234567890",
        phone_verified=True
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
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"  # Longer expiration for tests
    
    yield
    
    # Cleanup
    for key in ["TESTING", "DATABASE_URL", "REDIS_URL", "SECRET_KEY", "GEMINI_API_KEY", "STRIPE_API_KEY", "ENVIRONMENT", "ACCESS_TOKEN_EXPIRE_MINUTES"]:
        if key in os.environ:
            del os.environ[key]

# Global mocking to prevent heavy model loading and external service calls
@pytest.fixture(autouse=True)
def mock_heavy_services():
    """Mock heavy services that cause tests to hang."""
    
    # Mock sentence transformers to prevent model downloading
    with patch('sentence_transformers.SentenceTransformer') as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]  # Mock 384-dim embedding
        mock_st.return_value = mock_model
        
        # Mock cross encoder
        with patch('sentence_transformers.CrossEncoder') as mock_ce:
            mock_ce_model = MagicMock()
            mock_ce_model.predict.return_value = [0.8]  # Mock score
            mock_ce.return_value = mock_ce_model
            
            # Mock Redis manager to prevent connection attempts
            with patch('app.core.database.RedisManager') as mock_redis_manager:
                mock_redis_client = MagicMock()
                mock_redis_client.ping.return_value = True
                mock_redis_client.get.return_value = None
                mock_redis_client.set.return_value = True
                mock_redis_client.delete.return_value = True
                mock_redis_client.exists.return_value = False
                mock_redis_client.incr.return_value = 1
                mock_redis_client.expire.return_value = True
                mock_redis_manager.return_value.get_client.return_value = mock_redis_client
                mock_redis_manager.return_value.health_check.return_value = True
                
                # Mock httpx for external API calls
                with patch('httpx.AsyncClient') as mock_httpx:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "ok"}
                    mock_response.text = "OK"
                    mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
                    mock_httpx.return_value.__aenter__.return_value.post.return_value = mock_response
                    
                    # Mock production RAG system initialization
                    with patch('app.services.production_rag_system.production_file_processor') as mock_rag:
                        mock_rag_instance = MagicMock()
                        mock_rag_instance.process_file.return_value = []
                        mock_rag_instance.create_semantic_chunks.return_value = []
                        mock_rag.return_value = mock_rag_instance
                        
                        # Mock A/B testing service
                        with patch('app.services.ab_testing_service.ABTestingService') as mock_ab:
                            mock_ab_instance = MagicMock()
                            mock_ab_instance.load_tests.return_value = []
                            mock_ab.return_value = mock_ab_instance
                            
                            yield

# CI/test hardening: block external network and enforce short HTTP client timeouts
import socket
import httpx
import functools

_LOCALHOST = {"127.0.0.1", "::1", "localhost"}

@pytest.fixture(scope="session", autouse=True)
def ci_sandbox():
    """Harden CI/test runs to avoid external stalls and enforce strict timeouts.
    - Sets stable testing env vars
    - Blocks outbound network except localhost
    - Forces httpx clients to use short default timeouts
    """
    # Env hardening
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("ENVIRONMENT", "testing")
    os.environ.setdefault("PYTHONFAULTHANDLER", "1")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_MAX_THREADS", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    # Block external network (allow localhost only)
    real_connect = socket.socket.connect
    def guarded_connect(self, address):
        try:
            host = address[0]
        except Exception:
            host = None
        if host not in _LOCALHOST:
            raise RuntimeError(f"Network blocked in CI tests: {host}")
        return real_connect(self, address)

    # Force short httpx timeouts by default
    orig_client_init = httpx.Client.__init__
    orig_async_init = httpx.AsyncClient.__init__

    @functools.wraps(orig_client_init)
    def client_init(self, *args, timeout=None, **kwargs):
        if timeout is None:
            timeout = 2.0
        return orig_client_init(self, *args, timeout=timeout, **kwargs)

    @functools.wraps(orig_async_init)
    def async_init(self, *args, timeout=None, **kwargs):
        if timeout is None:
            timeout = 2.0
        return orig_async_init(self, *args, timeout=timeout, **kwargs)

    # Apply patches
    socket.socket.connect = guarded_connect  # type: ignore[assignment]
    httpx.Client.__init__ = client_init  # type: ignore[assignment]
    httpx.AsyncClient.__init__ = async_init  # type: ignore[assignment]

    try:
        yield
    finally:
        # Restore originals
        socket.socket.connect = real_connect  # type: ignore[assignment]
        httpx.Client.__init__ = orig_client_init  # type: ignore[assignment]
        httpx.AsyncClient.__init__ = orig_async_init  # type: ignore[assignment]

import pytest

try:
    from tests.conftest import db_session as _db_session  # type: ignore
except Exception:  # pragma: no cover
    _db_session = None

@pytest.fixture
def test_db(db_session):  # type: ignore
    """Provide a real SQLAlchemy session for tests that request test_db."""
    return db_session
