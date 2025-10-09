"""
Unit tests for Model Validation
Tests all Pydantic models and SQLAlchemy models for proper validation
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage
from app.models.embed import EmbedCode, WidgetAsset
from app.models.subscriptions import Subscription
from app.models.team_member import TeamMember
from app.models.performance import (
    PerformanceMetric, PerformanceAlert, PerformanceConfig, 
    PerformanceReport, PerformanceBenchmark
)

from app.schemas.auth import (
    Token, TokenRefresh, TokenData, RegisterRequest, OTPRequest
)
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatResponse
from app.schemas.embed import EmbedCodeCreate, EmbedCodeUpdate, EmbedCodeResponse
from app.schemas.billing import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSource
from app.schemas.analytics import AnalyticsRequest, AnalyticsResponse, AnalyticsFilter
from app.schemas.performance import PerformanceMetricsRequest, PerformanceMetricsResponse

class TestUserModel:
    """Unit tests for User model"""
    
    def test_user_creation(self, db_session):
        """Test user model creation"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            workspace_id="ws_123",
            is_active=True
        )
        
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.full_name == "Test User"
        assert user.workspace_id == "ws_123"
        assert user.is_active is True
        assert user.id is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_email_validation(self, db_session):
        """Test user email validation"""
        # Valid email
        user = User(
            email="valid@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            workspace_id="ws_123"
        )
        assert user.email == "valid@example.com"
        
        # Invalid email should raise validation error
        with pytest.raises(ValidationError):
            User(
                email="invalid-email",
                hashed_password="hashed_password",
                full_name="Test User",
                workspace_id="ws_123"
            )
    
    def test_user_password_requirements(self, db_session):
        """Test user password requirements"""
        # Test with valid password
        user = User(
            email="test@example.com",
            hashed_password="$pbkdf2-sha256$valid_hash",
            full_name="Test User",
            workspace_id="ws_123"
        )
        assert user.hashed_password.startswith("$pbkdf2-sha256$")
    
    def test_user_workspace_relationship(self, db_session):
        """Test user-workspace relationship"""
        workspace = Workspace(
            name="Test Workspace",
            custom_domain="test.com"
        )
        db_session.add(workspace)
        db_session.flush()
        
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            workspace_id=workspace.id
        )
        
        assert user.workspace_id == workspace.id

class TestWorkspaceModel:
    """Unit tests for Workspace model"""
    
    def test_workspace_creation(self, db_session):
        """Test workspace model creation"""
        workspace = Workspace(
            name="Test Workspace",
            custom_domain="test.example.com",
            is_active=True
        )
        
        assert workspace.name == "Test Workspace"
        assert workspace.custom_domain == "test.example.com"
        assert workspace.is_active is True
        assert workspace.id is not None
        assert isinstance(workspace.created_at, datetime)
    
    def test_workspace_domain_validation(self, db_session):
        """Test workspace domain validation"""
        # Valid domain
        workspace = Workspace(
            name="Test Workspace",
            custom_domain="valid-domain.com"
        )
        assert workspace.custom_domain == "valid-domain.com"
        
        # Invalid domain format
        with pytest.raises(ValidationError):
            Workspace(
                name="Test Workspace",
                custom_domain="invalid-domain"
            )
    
    def test_workspace_name_required(self, db_session):
        """Test that workspace name is required"""
        with pytest.raises(ValidationError):
            Workspace(
                custom_domain="test.com"
                # Missing name
            )

class TestDocumentModel:
    """Unit tests for Document model"""
    
    def test_document_creation(self, db_session):
        """Test document model creation"""
        document = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            file_type="application/pdf",
            status="processed",
            user_id="user_123",
            workspace_id="ws_123"
        )
        
        assert document.filename == "test.pdf"
        assert document.file_path == "/tmp/test.pdf"
        assert document.file_size == 1024
        assert document.file_type == "application/pdf"
        assert document.status == "processed"
        assert document.user_id == "user_123"
        assert document.workspace_id == "ws_123"
        assert document.id is not None
        assert isinstance(document.created_at, datetime)
    
    def test_document_status_validation(self, db_session):
        """Test document status validation"""
        # Valid status
        document = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            file_type="application/pdf",
            status="processing",
            user_id="user_123",
            workspace_id="ws_123"
        )
        assert document.status == "processing"
        
        # Invalid status should raise validation error
        with pytest.raises(ValidationError):
            Document(
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                file_type="application/pdf",
                status="invalid_status",
                user_id="user_123",
                workspace_id="ws_123"
            )
    
    def test_document_file_type_validation(self, db_session):
        """Test document file type validation"""
        # Valid file types
        valid_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
        for file_type in valid_types:
            document = Document(
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                file_type=file_type,
                status="processed",
                user_id="user_123",
                workspace_id="ws_123"
            )
            assert document.file_type == file_type

class TestDocumentChunkModel:
    """Unit tests for DocumentChunk model"""
    
    def test_document_chunk_creation(self, db_session):
        """Test document chunk model creation"""
        chunk = DocumentChunk(
            document_id="doc_123",
            content="This is a test chunk of content.",
            chunk_index=0,
            metadata={"source": "test.pdf", "page": 1}
        )
        
        assert chunk.document_id == "doc_123"
        assert chunk.content == "This is a test chunk of content."
        assert chunk.chunk_index == 0
        assert chunk.metadata == {"source": "test.pdf", "page": 1}
        assert chunk.id is not None
        assert isinstance(chunk.created_at, datetime)
    
    def test_document_chunk_metadata_validation(self, db_session):
        """Test document chunk metadata validation"""
        # Valid metadata
        chunk = DocumentChunk(
            document_id="doc_123",
            content="Test content",
            chunk_index=0,
            metadata={"source": "test.pdf", "page": 1, "score": 0.95}
        )
        assert chunk.metadata["score"] == 0.95
        
        # Empty metadata should be allowed
        chunk = DocumentChunk(
            document_id="doc_123",
            content="Test content",
            chunk_index=0,
            metadata={}
        )
        assert chunk.metadata == {}

class TestChatSessionModel:
    """Unit tests for ChatSession model"""
    
    def test_chat_session_creation(self, db_session):
        """Test chat session model creation"""
        session = ChatSession(
            user_id="user_123",
            workspace_id="ws_123",
            user_label="Test Customer",
            is_active=True
        )
        
        assert session.user_id == "user_123"
        assert session.workspace_id == "ws_123"
        assert session.user_label == "Test Customer"
        assert session.is_active is True
        assert session.id is not None
        assert isinstance(session.created_at, datetime)
    
    def test_chat_session_user_label_optional(self, db_session):
        """Test that user label is optional"""
        session = ChatSession(
            user_id="user_123",
            workspace_id="ws_123"
            # user_label is optional
        )
        
        assert session.user_label is None
        assert session.user_id == "user_123"

class TestChatMessageModel:
    """Unit tests for ChatMessage model"""
    
    def test_chat_message_creation(self, db_session):
        """Test chat message model creation"""
        message = ChatMessage(
            session_id="session_123",
            role="user",
            content="Hello, how can I help you?",
            metadata={"tokens_used": 10}
        )
        
        assert message.session_id == "session_123"
        assert message.role == "user"
        assert message.content == "Hello, how can I help you?"
        assert message.metadata == {"tokens_used": 10}
        assert message.id is not None
        assert isinstance(message.created_at, datetime)
    
    def test_chat_message_role_validation(self, db_session):
        """Test chat message role validation"""
        # Valid roles
        valid_roles = ["user", "assistant", "system"]
        
        for role in valid_roles:
            message = ChatMessage(
                session_id="session_123",
                role=role,
                content="Test message"
            )
            assert message.role == role
        
        # Invalid role should raise validation error
        with pytest.raises(ValidationError):
            ChatMessage(
                session_id="session_123",
                role="invalid_role",
                content="Test message"
            )

class TestEmbedCodeModel:
    """Unit tests for EmbedCode model"""
    
    def test_embed_code_creation(self, db_session):
        """Test embed code model creation"""
        embed_code = EmbedCode(
            workspace_id="ws_123",
            user_id="user_123",
            snippet_template="<script>console.log('test')</script>",
            default_config={"theme": {"primary": "#4f46e5"}},
            client_api_key="api_key_123",
            is_active=True
        )
        
        assert embed_code.workspace_id == "ws_123"
        assert embed_code.user_id == "user_123"
        assert embed_code.snippet_template == "<script>console.log('test')</script>"
        assert embed_code.default_config == {"theme": {"primary": "#4f46e5"}}
        assert embed_code.client_api_key == "api_key_123"
        assert embed_code.is_active is True
        assert embed_code.id is not None
        assert isinstance(embed_code.created_at, datetime)
    
    def test_embed_code_config_validation(self, db_session):
        """Test embed code configuration validation"""
        # Valid config
        embed_code = EmbedCode(
            workspace_id="ws_123",
            user_id="user_123",
            snippet_template="<script>test</script>",
            default_config={
                "theme": {"primary": "#4f46e5", "secondary": "#6b7280"},
                "position": "bottom-right",
                "welcomeMessage": "Hello!"
            }
        )
        assert embed_code.default_config["theme"]["primary"] == "#4f46e5"

class TestSubscriptionModel:
    """Unit tests for Subscription model"""
    
    def test_subscription_creation(self, db_session):
        """Test subscription model creation"""
        subscription = Subscription(
            workspace_id="ws_123",
            tier="pro",
            status="active",
            monthly_query_quota=10000,
            queries_this_period=500,
            period_start=datetime.now(),
            period_end=datetime.now() + timedelta(days=30)
        )
        
        assert subscription.workspace_id == "ws_123"
        assert subscription.tier == "pro"
        assert subscription.status == "active"
        assert subscription.monthly_query_quota == 10000
        assert subscription.queries_this_period == 500
        assert subscription.id is not None
        assert isinstance(subscription.created_at, datetime)
    
    def test_subscription_tier_validation(self, db_session):
        """Test subscription tier validation"""
        # Valid tiers
        valid_tiers = ["free", "pro", "enterprise"]
        
        for tier in valid_tiers:
            subscription = Subscription(
                workspace_id="ws_123",
                tier=tier,
                status="active",
                monthly_query_quota=1000,
                queries_this_period=0,
                period_start=datetime.now(),
                period_end=datetime.now() + timedelta(days=30)
            )
            assert subscription.tier == tier
        
        # Invalid tier should raise validation error
        with pytest.raises(ValidationError):
            Subscription(
                workspace_id="ws_123",
                tier="invalid_tier",
                status="active",
                monthly_query_quota=1000,
                queries_this_period=0,
                period_start=datetime.now(),
                period_end=datetime.now() + timedelta(days=30)
            )

class TestTeamMemberModel:
    """Unit tests for TeamMember model"""
    
    def test_team_member_creation(self, db_session):
        """Test team member model creation"""
        team_member = TeamMember(
            workspace_id="ws_123",
            user_id="user_123",
            role="admin",
            permissions=["read", "write", "delete"],
            is_active=True
        )
        
        assert team_member.workspace_id == "ws_123"
        assert team_member.user_id == "user_123"
        assert team_member.role == "admin"
        assert team_member.permissions == ["read", "write", "delete"]
        assert team_member.is_active is True
        assert team_member.id is not None
        assert isinstance(team_member.created_at, datetime)
    
    def test_team_member_role_validation(self, db_session):
        """Test team member role validation"""
        # Valid roles
        valid_roles = ["admin", "member", "viewer"]
        
        for role in valid_roles:
            team_member = TeamMember(
                workspace_id="ws_123",
                user_id="user_123",
                role=role,
                permissions=["read"]
            )
            assert team_member.role == role

class TestPerformanceModels:
    """Unit tests for Performance models"""
    
    def test_performance_metric_creation(self, db_session):
        """Test performance metric model creation"""
        metric = PerformanceMetric(
            workspace_id="ws_123",
            metric_name="response_time",
            metric_value=150.5,
            metric_unit="ms",
            timestamp=datetime.now()
        )
        
        assert metric.workspace_id == "ws_123"
        assert metric.metric_name == "response_time"
        assert metric.metric_value == 150.5
        assert metric.metric_unit == "ms"
        assert metric.id is not None
        assert isinstance(metric.created_at, datetime)
    
    def test_performance_alert_creation(self, db_session):
        """Test performance alert model creation"""
        alert = PerformanceAlert(
            workspace_id="ws_123",
            alert_type="high_response_time",
            threshold_value=1000.0,
            current_value=1500.0,
            severity="high",
            is_resolved=False
        )
        
        assert alert.workspace_id == "ws_123"
        assert alert.alert_type == "high_response_time"
        assert alert.threshold_value == 1000.0
        assert alert.current_value == 1500.0
        assert alert.severity == "high"
        assert alert.is_resolved is False
        assert alert.id is not None
        assert isinstance(alert.created_at, datetime)
    
    def test_performance_config_creation(self, db_session):
        """Test performance configuration model creation"""
        config = PerformanceConfig(
            workspace_id="ws_123",
            config_name="response_time_threshold",
            config_value=1000.0,
            config_type="threshold",
            is_active=True
        )
        
        assert config.workspace_id == "ws_123"
        assert config.config_name == "response_time_threshold"
        assert config.config_value == 1000.0
        assert config.config_type == "threshold"
        assert config.is_active is True
        assert config.id is not None
        assert isinstance(config.created_at, datetime)

class TestAuthSchemas:
    """Unit tests for Authentication schemas"""
    
    def test_token_schema(self):
        """Test Token schema validation"""
        token_data = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "token_type": "bearer",
            "expires_in": 3600
        }
        
        token = Token(**token_data)
        assert token.access_token == "access_token_123"
        assert token.refresh_token == "refresh_token_123"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
    
    def test_register_request_schema(self):
        """Test RegisterRequest schema validation"""
        register_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "business_name": "Test Business",
            "business_domain": "test.com",
            "mobile_phone": "+1234567890",
            "otp_code": "123456"
        }
        
        register_request = RegisterRequest(**register_data)
        assert register_request.email == "test@example.com"
        assert register_request.password == "SecurePassword123!"
        assert register_request.full_name == "Test User"
        assert register_request.business_name == "Test Business"
        assert register_request.business_domain == "test.com"
        assert register_request.mobile_phone == "+1234567890"
        assert register_request.otp_code == "123456"
    
    def test_register_request_email_validation(self):
        """Test RegisterRequest email validation"""
        # Valid email
        register_data = {
            "email": "valid@example.com",
            "password": "SecurePassword123!",
            "mobile_phone": "+1234567890",
            "otp_code": "123456"
        }
        
        register_request = RegisterRequest(**register_data)
        assert register_request.email == "valid@example.com"
        
        # Invalid email should raise validation error
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="invalid-email",
                password="SecurePassword123!",
                mobile_phone="+1234567890",
                otp_code="123456"
            )

class TestRAGSchemas:
    """Unit tests for RAG schemas"""
    
    def test_rag_query_request_schema(self):
        """Test RAGQueryRequest schema validation"""
        query_data = {
            "query": "What is your refund policy?",
            "session_id": "session_123",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        query_request = RAGQueryRequest(**query_data)
        assert query_request.query == "What is your refund policy?"
        assert query_request.session_id == "session_123"
        assert query_request.max_tokens == 1000
        assert query_request.temperature == 0.7
    
    def test_rag_query_response_schema(self):
        """Test RAGQueryResponse schema validation"""
        response_data = {
            "answer": "Our refund policy allows returns within 30 days.",
            "sources": [
                {
                    "chunk_id": "chunk_123",
                    "document_id": "doc_456",
                    "content": "Refund policy content",
                    "score": 0.95
                }
            ],
            "response_time_ms": 150,
            "tokens_used": 100
        }
        
        query_response = RAGQueryResponse(**response_data)
        assert query_response.answer == "Our refund policy allows returns within 30 days."
        assert len(query_response.sources) == 1
        assert query_response.sources[0].chunk_id == "chunk_123"
        assert query_response.response_time_ms == 150
        assert query_response.tokens_used == 100
    
    def test_rag_source_schema(self):
        """Test RAGSource schema validation"""
        source_data = {
            "chunk_id": "chunk_123",
            "document_id": "doc_456",
            "content": "Source content",
            "score": 0.95,
            "metadata": {"page": 1, "section": "refund_policy"}
        }
        
        source = RAGSource(**source_data)
        assert source.chunk_id == "chunk_123"
        assert source.document_id == "doc_456"
        assert source.content == "Source content"
        assert source.score == 0.95
        assert source.metadata == {"page": 1, "section": "refund_policy"}

class TestAnalyticsSchemas:
    """Unit tests for Analytics schemas"""
    
    def test_analytics_request_schema(self):
        """Test AnalyticsRequest schema validation"""
        request_data = {
            "workspace_id": "ws_123",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "metrics": ["queries", "documents", "response_time"],
            "group_by": "day"
        }
        
        analytics_request = AnalyticsRequest(**request_data)
        assert analytics_request.workspace_id == "ws_123"
        assert analytics_request.start_date == "2024-01-01"
        assert analytics_request.end_date == "2024-01-31"
        assert analytics_request.metrics == ["queries", "documents", "response_time"]
        assert analytics_request.group_by == "day"
    
    def test_analytics_filter_schema(self):
        """Test AnalyticsFilter schema validation"""
        filter_data = {
            "user_id": "user_123",
            "document_id": "doc_456",
            "session_id": "session_789",
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
        }
        
        analytics_filter = AnalyticsFilter(**filter_data)
        assert analytics_filter.user_id == "user_123"
        assert analytics_filter.document_id == "doc_456"
        assert analytics_filter.session_id == "session_789"
        assert analytics_filter.date_range["start"] == "2024-01-01"
        assert analytics_filter.date_range["end"] == "2024-01-31"

class TestPerformanceSchemas:
    """Unit tests for Performance schemas"""
    
    def test_performance_metrics_request_schema(self):
        """Test PerformanceMetricsRequest schema validation"""
        request_data = {
            "workspace_id": "ws_123",
            "metric_names": ["response_time", "throughput", "error_rate"],
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-01T23:59:59Z",
            "aggregation": "avg"
        }
        
        metrics_request = PerformanceMetricsRequest(**request_data)
        assert metrics_request.workspace_id == "ws_123"
        assert metrics_request.metric_names == ["response_time", "throughput", "error_rate"]
        assert metrics_request.start_time == "2024-01-01T00:00:00Z"
        assert metrics_request.end_time == "2024-01-01T23:59:59Z"
        assert metrics_request.aggregation == "avg"
    
    def test_performance_metrics_response_schema(self):
        """Test PerformanceMetricsResponse schema validation"""
        response_data = {
            "workspace_id": "ws_123",
            "metrics": {
                "response_time": {"avg": 150.5, "max": 300.0, "min": 50.0},
                "throughput": {"avg": 100.0, "max": 200.0, "min": 50.0}
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        metrics_response = PerformanceMetricsResponse(**response_data)
        assert metrics_response.workspace_id == "ws_123"
        assert "response_time" in metrics_response.metrics
        assert "throughput" in metrics_response.metrics
        assert metrics_response.metrics["response_time"]["avg"] == 150.5
        assert metrics_response.timestamp == "2024-01-01T12:00:00Z"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

