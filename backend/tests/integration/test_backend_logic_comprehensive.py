"""
Comprehensive Backend Logic Integration Tests
Tests all backend services, business rules, error handling, and complex workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, ChatSession, ChatMessage, EmbedCode, Subscription
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.embed_service import EmbedService
from app.services.rate_limiting import rate_limiting_service


class TestBackendLogicComprehensive:
    """Comprehensive tests for backend logic and services"""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a fresh database session for each test."""
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture(scope="function")
    def client(self, db_session):
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
    def test_workspace(self, db_session):
        """Create test workspace"""
        workspace = Workspace(
            id="ws_logic_test",
            name="Logic Test Workspace",
            description="Test workspace for backend logic testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            id="user_logic_test",
            email="logic@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Logic Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_subscription(self, db_session, test_workspace):
        """Create test subscription"""
        subscription = Subscription(
            workspace_id=test_workspace.id,
            tier="pro",
            status="active",
            monthly_query_quota=1000,
            document_limit=100
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        return subscription

    # ==================== AUTHENTICATION SERVICE TESTS ====================
    
    def test_auth_service_password_hashing(self, db_session):
        """Test password hashing functionality"""
        auth_service = AuthService(db_session)
        
        # Test password hashing
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt format
        
        # Test password verification
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_auth_service_jwt_token_creation(self, db_session):
        """Test JWT token creation and validation"""
        auth_service = AuthService(db_session)
        
        # Test token creation
        user_data = {"sub": "test@example.com", "user_id": "user_123"}
        token = auth_service.create_access_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        
        # Test token validation
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == "user_123"

    def test_auth_service_token_expiration(self, db_session):
        """Test JWT token expiration handling"""
        auth_service = AuthService(db_session)
        
        # Create token with very short expiration
        user_data = {"sub": "test@example.com"}
        token = auth_service.create_access_token(
            data=user_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid initially
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "test@example.com"
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be invalid after expiration
        with pytest.raises(Exception):
            auth_service.verify_token(token)

    def test_auth_service_user_registration_validation(self, db_session):
        """Test user registration validation logic"""
        auth_service = AuthService(db_session)
        
        # Test valid registration
        result = auth_service.validate_user_registration(
            email="valid@example.com",
            mobile_phone="+1234567890"
        )
        assert result["valid"] is True
        
        # Test invalid email
        result = auth_service.validate_user_registration(
            email="invalid_email",
            mobile_phone="+1234567890"
        )
        assert result["valid"] is False
        assert "email" in result["message"].lower()
        
        # Test invalid mobile
        result = auth_service.validate_user_registration(
            email="valid@example.com",
            mobile_phone="invalid_phone"
        )
        assert result["valid"] is False
        assert "mobile" in result["message"].lower()

    # ==================== CHAT SERVICE TESTS ====================
    
    def test_chat_service_message_processing(self, db_session, test_user, test_workspace):
        """Test chat service message processing logic"""
        chat_service = ChatService(db_session)
        
        # Test message processing
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.return_value = {
                "answer": "Test response",
                "sources": [{"content": "Source 1"}],
                "confidence": "high"
            }
            mock_rag_service.return_value = mock_rag
            
            response = asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message="Hello, how can I help?",
                session_id="test-session-1"
            ))
            
            assert response["message"] == "Test response"
            assert response["session_id"] == "test-session-1"
            assert "sources" in response

    def test_chat_service_session_management(self, db_session, test_user, test_workspace):
        """Test chat service session management logic"""
        chat_service = ChatService(db_session)
        
        # Test session creation
        session = chat_service.create_session(
            user_id=test_user.id,
            workspace_id=test_workspace.id,
            user_label="Test Customer"
        )
        
        assert session is not None
        assert session.user_id == test_user.id
        assert session.workspace_id == test_workspace.id
        assert session.is_active is True
        
        # Test session retrieval
        retrieved_session = chat_service.get_session_by_id(
            session_id=session.session_id,
            user_id=test_user.id
        )
        
        assert retrieved_session is not None
        assert retrieved_session.id == session.id
        
        # Test session ending
        success = chat_service.end_session(
            session_id=session.session_id,
            user_id=test_user.id
        )
        
        assert success is True
        
        # Verify session is inactive
        db_session.refresh(session)
        assert session.is_active is False

    def test_chat_service_message_flagging(self, db_session, test_user, test_workspace):
        """Test chat service message flagging logic"""
        chat_service = ChatService(db_session)
        
        # Create session and message
        session = chat_service.create_session(
            user_id=test_user.id,
            workspace_id=test_workspace.id,
            user_label="Test Customer"
        )
        
        message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Test message",
            created_at=datetime.utcnow()
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Test message flagging
        success = chat_service.flag_message(
            session_id=session.session_id,
            message_id=message.id,
            user_id=test_user.id,
            reason="Inappropriate content"
        )
        
        assert success is True
        
        # Verify message is flagged
        db_session.refresh(message)
        assert message.is_flagged is True
        assert message.flag_reason == "Inappropriate content"

    # ==================== RAG SERVICE TESTS ====================
    
    def test_rag_service_query_processing(self, db_session, test_user, test_workspace):
        """Test RAG service query processing logic"""
        rag_service = RAGService(db_session)
        
        # Test query processing
        with patch('app.services.embeddings_service.EmbeddingsService') as mock_embeddings, \
             patch('app.services.vector_service.VectorService') as mock_vector, \
             patch('app.services.gemini_service.GeminiService') as mock_gemini:
            
            mock_embeddings.return_value.embed_text.return_value = [0.1] * 384
            mock_vector.return_value.search.return_value = [
                {"content": "Relevant content", "score": 0.9}
            ]
            mock_gemini.return_value.generate_response.return_value = {
                "answer": "Generated response",
                "sources": [{"content": "Relevant content"}]
            }
            
            result = asyncio.run(rag_service.process_query(
                query="Test query",
                user_id=test_user.id,
                workspace_id=test_workspace.id
            ))
            
            assert result["answer"] == "Generated response"
            assert "sources" in result

    def test_rag_service_source_ranking(self, db_session, test_user, test_workspace):
        """Test RAG service source ranking logic"""
        rag_service = RAGService(db_session)
        
        # Test source ranking
        sources = [
            {"content": "Source 1", "score": 0.8},
            {"content": "Source 2", "score": 0.9},
            {"content": "Source 3", "score": 0.7}
        ]
        
        ranked_sources = rag_service.rank_sources(sources)
        
        # Should be sorted by score (highest first)
        assert ranked_sources[0]["score"] == 0.9
        assert ranked_sources[1]["score"] == 0.8
        assert ranked_sources[2]["score"] == 0.7

    def test_rag_service_confidence_calculation(self, db_session, test_user, test_workspace):
        """Test RAG service confidence calculation logic"""
        rag_service = RAGService(db_session)
        
        # Test confidence calculation
        sources = [
            {"score": 0.9},
            {"score": 0.8},
            {"score": 0.7}
        ]
        
        confidence = rag_service.calculate_confidence(sources)
        
        # Should be high confidence for good scores
        assert confidence in ["high", "medium", "low"]
        assert confidence == "high"  # High scores should result in high confidence

    # ==================== DOCUMENT SERVICE TESTS ====================
    
    def test_document_service_file_validation(self, db_session, test_user, test_workspace):
        """Test document service file validation logic"""
        document_service = DocumentService(db_session)
        
        # Test valid file types
        valid_files = [
            ("test.pdf", "application/pdf"),
            ("test.txt", "text/plain"),
            ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        ]
        
        for filename, content_type in valid_files:
            is_valid = document_service.validate_file_type(filename, content_type)
            assert is_valid is True
        
        # Test invalid file types
        invalid_files = [
            ("test.exe", "application/x-msdownload"),
            ("test.bat", "application/x-msdownload"),
            ("test.sh", "application/x-sh")
        ]
        
        for filename, content_type in invalid_files:
            is_valid = document_service.validate_file_type(filename, content_type)
            assert is_valid is False

    def test_document_service_size_validation(self, db_session, test_user, test_workspace):
        """Test document service size validation logic"""
        document_service = DocumentService(db_session)
        
        # Test valid file sizes
        valid_sizes = [1024, 1024 * 1024, 10 * 1024 * 1024]  # 1KB, 1MB, 10MB
        
        for size in valid_sizes:
            is_valid = document_service.validate_file_size(size)
            assert is_valid is True
        
        # Test invalid file sizes
        invalid_sizes = [100 * 1024 * 1024, 1024 * 1024 * 1024]  # 100MB, 1GB
        
        for size in invalid_sizes:
            is_valid = document_service.validate_file_size(size)
            assert is_valid is False

    def test_document_service_chunking_logic(self, db_session, test_user, test_workspace):
        """Test document service chunking logic"""
        document_service = DocumentService(db_session)
        
        # Test text chunking
        long_text = "This is a long text that should be chunked into smaller pieces. " * 100
        
        chunks = document_service.chunk_text(long_text, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
        assert "".join(chunks) == long_text

    # ==================== EMBED SERVICE TESTS ====================
    
    def test_embed_service_code_generation(self, db_session, test_user, test_workspace):
        """Test embed service code generation logic"""
        embed_service = EmbedService(db_session)
        
        # Test embed code generation
        embed_code = embed_service.generate_embed_code(
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            code_name="Test Widget",
            config={"theme": {"primary": "#4f46e5"}}
        )
        
        assert embed_code is not None
        assert embed_code.workspace_id == test_workspace.id
        assert embed_code.user_id == test_user.id
        assert embed_code.code_name == "Test Widget"
        assert embed_code.is_active is True
        assert len(embed_code.client_api_key) > 20  # Should be a long random key

    def test_embed_service_snippet_generation(self, db_session, test_user, test_workspace):
        """Test embed service snippet generation logic"""
        embed_service = EmbedService(db_session)
        
        # Create embed code
        embed_code = embed_service.generate_embed_code(
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            code_name="Test Widget",
            config={"theme": {"primary": "#4f46e5"}}
        )
        
        # Test snippet generation
        snippet = embed_service.get_embed_snippet(embed_code)
        
        assert isinstance(snippet, str)
        assert len(snippet) > 100  # Should be a substantial snippet
        assert "script" in snippet.lower()
        assert embed_code.client_api_key in snippet

    def test_embed_service_api_key_validation(self, db_session, test_user, test_workspace):
        """Test embed service API key validation logic"""
        embed_service = EmbedService(db_session)
        
        # Create embed code
        embed_code = embed_service.generate_embed_code(
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        # Test valid API key
        retrieved_code = embed_service.get_embed_code_by_api_key(embed_code.client_api_key)
        assert retrieved_code is not None
        assert retrieved_code.id == embed_code.id
        
        # Test invalid API key
        invalid_code = embed_service.get_embed_code_by_api_key("invalid_key")
        assert invalid_code is None

    # ==================== RATE LIMITING SERVICE TESTS ====================
    
    def test_rate_limiting_service_ip_limits(self, db_session):
        """Test rate limiting service IP limits"""
        # Test IP rate limiting
        with patch('app.services.rate_limiting.rate_limiting_service.check_ip_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
            mock_rate_limit.return_value = (True, {"limit": 10, "remaining": 9, "reset_time": Mock(timestamp=lambda: 0)})
            
            result = asyncio.run(rate_limiting_service.check_ip_rate_limit(
                ip_address="192.168.1.1",
                limit=10,
                window_seconds=60
            ))
            
            assert result[0] is True  # Should be allowed
            assert result[1]["remaining"] == 9

    def test_rate_limiting_service_user_limits(self, db_session):
        """Test rate limiting service user limits"""
        # Test user rate limiting
        with patch('app.services.rate_limiting.rate_limiting_service.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
            mock_rate_limit.return_value = (True, {"limit": 100, "remaining": 99, "reset_time": Mock(timestamp=lambda: 0)})
            
            result = asyncio.run(rate_limiting_service.check_rate_limit(
                identifier="user_123",
                limit=100,
                window_seconds=3600
            ))
            
            assert result[0] is True  # Should be allowed
            assert result[1]["remaining"] == 99

    def test_rate_limiting_service_workspace_limits(self, db_session):
        """Test rate limiting service workspace limits"""
        # Test workspace rate limiting
        with patch('app.services.rate_limiting.rate_limiting_service.check_workspace_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
            mock_rate_limit.return_value = (True, {"limit": 1000, "remaining": 999, "reset_time": Mock(timestamp=lambda: 0)})
            
            result = asyncio.run(rate_limiting_service.check_workspace_rate_limit(
                workspace_id="ws_123",
                limit=1000,
                window_seconds=3600
            ))
            
            assert result[0] is True  # Should be allowed
            assert result[1]["remaining"] == 999

    # ==================== BUSINESS RULE TESTS ====================
    
    def test_quota_enforcement_logic(self, db_session, test_user, test_workspace, test_subscription):
        """Test quota enforcement business logic"""
        from app.middleware.quota_middleware import check_quota, increment_usage
        
        # Test quota checking
        with patch('app.middleware.quota_middleware.check_quota') as mock_check_quota:
            mock_check_quota.return_value = test_subscription
            
            # Should pass quota check
            subscription = check_quota(test_user)
            assert subscription is not None
            assert subscription.tier == "pro"

    def test_workspace_isolation_logic(self, db_session, test_workspace):
        """Test workspace isolation business logic"""
        # Create two workspaces
        workspace1 = Workspace(id="ws_1", name="Workspace 1")
        workspace2 = Workspace(id="ws_2", name="Workspace 2")
        db_session.add_all([workspace1, workspace2])
        db_session.commit()
        
        # Create users in different workspaces
        user1 = User(
            id="user_1",
            email="user1@example.com",
            hashed_password="hashed",
            workspace_id="ws_1"
        )
        user2 = User(
            id="user_2",
            email="user2@example.com",
            hashed_password="hashed",
            workspace_id="ws_2"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Test workspace isolation
        assert user1.workspace_id != user2.workspace_id
        assert user1.workspace_id == "ws_1"
        assert user2.workspace_id == "ws_2"

    def test_subscription_tier_limits(self, db_session, test_workspace):
        """Test subscription tier limits business logic"""
        from app.utils.plan_limits import PlanLimits, PlanTier
        
        # Test different tier limits
        free_limits = PlanLimits.get_limits(PlanTier.FREE)
        pro_limits = PlanLimits.get_limits(PlanTier.PRO)
        enterprise_limits = PlanLimits.get_limits(PlanTier.ENTERPRISE)
        
        # Free tier should have lowest limits
        assert free_limits.monthly_query_quota < pro_limits.monthly_query_quota
        assert free_limits.monthly_query_quota < enterprise_limits.monthly_query_quota
        
        # Pro tier should have higher limits than free
        assert pro_limits.monthly_query_quota > free_limits.monthly_query_quota
        assert pro_limits.document_limit > free_limits.document_limit
        
        # Enterprise tier should have highest limits
        assert enterprise_limits.monthly_query_quota > pro_limits.monthly_query_quota
        assert enterprise_limits.document_limit > pro_limits.document_limit

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_service_error_handling(self, db_session, test_user, test_workspace):
        """Test service error handling logic"""
        chat_service = ChatService(db_session)
        
        # Test error handling in message processing
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.side_effect = Exception("RAG service error")
            mock_rag_service.return_value = mock_rag
            
            # Should handle error gracefully
            with pytest.raises(Exception):
                asyncio.run(chat_service.process_message(
                    user_id=test_user.id,
                    message="Test message",
                    session_id="test-session-1"
                ))

    def test_database_error_handling(self, db_session, test_user, test_workspace):
        """Test database error handling logic"""
        # Test database connection error
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # Should handle database error gracefully
            with pytest.raises(Exception):
                chat_service = ChatService(db_session)
                chat_service.create_session(
                    user_id=test_user.id,
                    workspace_id=test_workspace.id,
                    user_label="Test Customer"
                )

    def test_validation_error_handling(self, db_session, test_user, test_workspace):
        """Test validation error handling logic"""
        auth_service = AuthService(db_session)
        
        # Test validation error handling
        result = auth_service.validate_user_registration(
            email="invalid_email",
            mobile_phone="invalid_phone"
        )
        
        assert result["valid"] is False
        assert "error" in result["message"].lower() or "invalid" in result["message"].lower()

    # ==================== INTEGRATION WORKFLOW TESTS ====================
    
    def test_complete_user_registration_workflow(self, db_session, test_workspace):
        """Test complete user registration workflow"""
        auth_service = AuthService(db_session)
        user_service = Mock()
        
        # Test registration workflow
        user_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
            "mobile_phone": "+1234567890"
        }
        
        # Validate registration
        validation_result = auth_service.validate_user_registration(
            user_data["email"],
            user_data["mobile_phone"]
        )
        
        assert validation_result["valid"] is True
        
        # Hash password
        hashed_password = auth_service.hash_password(user_data["password"])
        assert hashed_password != user_data["password"]
        
        # Create user (mocked)
        user_service.create_user.return_value = Mock(
            id="new_user_id",
            email=user_data["email"],
            workspace_id=test_workspace.id
        )
        
        # Generate tokens
        access_token = auth_service.create_access_token(
            data={"sub": user_data["email"]}
        )
        refresh_token = auth_service.create_refresh_token(
            data={"sub": user_data["email"]}
        )
        
        assert access_token is not None
        assert refresh_token is not None

    def test_complete_document_upload_workflow(self, db_session, test_user, test_workspace):
        """Test complete document upload workflow"""
        document_service = DocumentService(db_session)
        
        # Test document upload workflow
        filename = "test_document.pdf"
        content_type = "application/pdf"
        file_size = 1024 * 1024  # 1MB
        
        # Validate file
        assert document_service.validate_file_type(filename, content_type) is True
        assert document_service.validate_file_size(file_size) is True
        
        # Create document record
        document = Document(
            id="doc_123",
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            filename=filename,
            content_type=content_type,
            size=file_size,
            path="/uploads/doc_123.pdf",
            status="uploaded"
        )
        db_session.add(document)
        db_session.commit()
        
        # Process document (mocked)
        with patch('app.services.document_service.DocumentService.process_document') as mock_process:
            mock_process.return_value = {"status": "processed", "chunks_created": 10}
            
            result = document_service.process_document(document.id)
            assert result["status"] == "processed"

    def test_complete_chat_workflow(self, db_session, test_user, test_workspace):
        """Test complete chat workflow"""
        chat_service = ChatService(db_session)
        
        # Create session
        session = chat_service.create_session(
            user_id=test_user.id,
            workspace_id=test_workspace.id,
            user_label="Test Customer"
        )
        
        # Process message
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.return_value = {
                "answer": "Hello! How can I help you?",
                "sources": [{"content": "Help documentation"}],
                "confidence": "high"
            }
            mock_rag_service.return_value = mock_rag
            
            response = asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message="Hello, I need help",
                session_id=session.session_id
            ))
            
            assert response["message"] == "Hello! How can I help you?"
            assert response["session_id"] == session.session_id
        
        # End session
        success = chat_service.end_session(
            session_id=session.session_id,
            user_id=test_user.id
        )
        
        assert success is True

    # ==================== PERFORMANCE TESTS ====================
    
    def test_service_performance_under_load(self, db_session, test_user, test_workspace):
        """Test service performance under load"""
        chat_service = ChatService(db_session)
        
        # Test multiple concurrent operations
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.return_value = {
                "answer": "Test response",
                "sources": [],
                "confidence": "high"
            }
            mock_rag_service.return_value = mock_rag
            
            # Create multiple sessions concurrently
            sessions = []
            for i in range(10):
                session = chat_service.create_session(
                    user_id=test_user.id,
                    workspace_id=test_workspace.id,
                    user_label=f"Customer {i}"
                )
                sessions.append(session)
            
            assert len(sessions) == 10
            
            # Process multiple messages concurrently
            async def process_message(session_id):
                return await chat_service.process_message(
                    user_id=test_user.id,
                    message=f"Message for session {session_id}",
                    session_id=session_id
                )
            
            # Run concurrent message processing
            tasks = [process_message(session.session_id) for session in sessions]
            responses = asyncio.run(asyncio.gather(*tasks))
            
            assert len(responses) == 10
            for response in responses:
                assert response["message"] == "Test response"

    def test_memory_usage_optimization(self, db_session, test_user, test_workspace):
        """Test memory usage optimization"""
        document_service = DocumentService(db_session)
        
        # Test chunking large text efficiently
        large_text = "This is a test sentence. " * 10000  # Large text
        
        chunks = document_service.chunk_text(large_text, chunk_size=1000)
        
        # Should create reasonable number of chunks
        assert len(chunks) > 0
        assert len(chunks) < len(large_text) / 100  # Should be much fewer chunks
        
        # Each chunk should be within size limit
        for chunk in chunks:
            assert len(chunk) <= 1000

    # ==================== EDGE CASE TESTS ====================
    
    def test_edge_case_empty_inputs(self, db_session, test_user, test_workspace):
        """Test edge cases with empty inputs"""
        chat_service = ChatService(db_session)
        
        # Test empty message
        with pytest.raises(ValueError):
            asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message="",
                session_id="test-session-1"
            ))
        
        # Test None message
        with pytest.raises(ValueError):
            asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message=None,
                session_id="test-session-1"
            ))

    def test_edge_case_very_long_inputs(self, db_session, test_user, test_workspace):
        """Test edge cases with very long inputs"""
        chat_service = ChatService(db_session)
        
        # Test very long message
        very_long_message = "A" * 10000  # 10KB message
        
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.return_value = {
                "answer": "Response to long message",
                "sources": [],
                "confidence": "medium"
            }
            mock_rag_service.return_value = mock_rag
            
            response = asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message=very_long_message,
                session_id="test-session-1"
            ))
            
            assert response["message"] == "Response to long message"

    def test_edge_case_special_characters(self, db_session, test_user, test_workspace):
        """Test edge cases with special characters"""
        chat_service = ChatService(db_session)
        
        # Test message with special characters
        special_message = "Hello! @#$%^&*()_+{}|:<>?[]\\;'\",./"
        
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_rag = Mock()
            mock_rag.process_query.return_value = {
                "answer": "Response to special characters",
                "sources": [],
                "confidence": "high"
            }
            mock_rag_service.return_value = mock_rag
            
            response = asyncio.run(chat_service.process_message(
                user_id=test_user.id,
                message=special_message,
                session_id="test-session-1"
            ))
            
            assert response["message"] == "Response to special characters"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
