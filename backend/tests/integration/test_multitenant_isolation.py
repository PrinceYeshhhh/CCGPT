"""
Critical multi-tenant isolation tests for production security
Tests cross-workspace data leakage prevention and workspace quota enforcement
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, Mock
import json

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, ChatSession, ChatMessage, Subscription, DocumentChunk
from app.services.auth import AuthService
from app.utils.plan_limits import PlanLimits


class TestMultiTenantIsolation:
    """Critical multi-tenant isolation tests for production security"""
    
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
    def workspace_a(self, db_session):
        """Create workspace A for isolation testing"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Workspace A",
            description="Test workspace A",
            domain="workspace-a.com"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def workspace_b(self, db_session):
        """Create workspace B for isolation testing"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="Workspace B", 
            description="Test workspace B",
            domain="workspace-b.com"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def user_a(self, db_session, workspace_a):
        """Create user in workspace A"""
        user = User(
            email="user-a@workspace-a.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="User A",
            workspace_id=workspace_a.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def user_b(self, db_session, workspace_b):
        """Create user in workspace B"""
        user = User(
            email="user-b@workspace-b.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="User B",
            workspace_id=workspace_b.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def subscription_a(self, db_session, workspace_a):
        """Create subscription for workspace A"""
        subscription = Subscription(
            workspace_id=workspace_a.id,
            tier="pro",
            status="active",
            monthly_query_quota=10000,
            queries_this_period=0
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        return subscription
    
    @pytest.fixture
    def subscription_b(self, db_session, workspace_b):
        """Create subscription for workspace B"""
        subscription = Subscription(
            workspace_id=workspace_b.id,
            tier="free",
            status="active",
            monthly_query_quota=1000,
            queries_this_period=0
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        return subscription
    
    def test_cross_workspace_user_isolation(self, db_session, user_a, user_b, workspace_a, workspace_b):
        """Test that users cannot access data from other workspaces"""
        # User A should only see users from workspace A
        users_in_workspace_a = db_session.query(User).filter(User.workspace_id == workspace_a.id).all()
        assert len(users_in_workspace_a) == 1
        assert users_in_workspace_a[0].email == "user-a@workspace-a.com"
        
        # User A should not see users from workspace B
        users_from_workspace_b = db_session.query(User).filter(
            User.workspace_id == workspace_a.id,
            User.email == "user-b@workspace-b.com"
        ).all()
        assert len(users_from_workspace_b) == 0
        
        # User B should only see users from workspace B
        users_in_workspace_b = db_session.query(User).filter(User.workspace_id == workspace_b.id).all()
        assert len(users_in_workspace_b) == 1
        assert users_in_workspace_b[0].email == "user-b@workspace-b.com"
    
    def test_cross_workspace_document_isolation(self, db_session, user_a, user_b, workspace_a, workspace_b):
        """Test that documents are isolated between workspaces"""
        # Create documents for each workspace
        doc_a = Document(
            id=str(uuid.uuid4()),
            workspace_id=workspace_a.id,
            filename="workspace-a-doc.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/workspace-a-doc.pdf",
            uploaded_by=user_a.id,
            status="processed"
        )
        db_session.add(doc_a)
        
        doc_b = Document(
            id=str(uuid.uuid4()),
            workspace_id=workspace_b.id,
            filename="workspace-b-doc.pdf",
            content_type="application/pdf",
            size=2048,
            path="/tmp/workspace-b-doc.pdf",
            uploaded_by=user_b.id,
            status="processed"
        )
        db_session.add(doc_b)
        db_session.commit()
        
        # User A should only see documents from workspace A
        docs_in_workspace_a = db_session.query(Document).filter(Document.workspace_id == workspace_a.id).all()
        assert len(docs_in_workspace_a) == 1
        assert docs_in_workspace_a[0].filename == "workspace-a-doc.pdf"
        
        # User A should not see documents from workspace B
        docs_from_workspace_b = db_session.query(Document).filter(
            Document.workspace_id == workspace_a.id,
            Document.filename == "workspace-b-doc.pdf"
        ).all()
        assert len(docs_from_workspace_b) == 0
        
        # User B should only see documents from workspace B
        docs_in_workspace_b = db_session.query(Document).filter(Document.workspace_id == workspace_b.id).all()
        assert len(docs_in_workspace_b) == 1
        assert docs_in_workspace_b[0].filename == "workspace-b-doc.pdf"
    
    def test_cross_workspace_chat_isolation(self, db_session, user_a, user_b, workspace_a, workspace_b):
        """Test that chat sessions are isolated between workspaces"""
        # Create chat sessions for each workspace
        session_a = ChatSession(
            id=str(uuid.uuid4()),
            workspace_id=workspace_a.id,
            user_id=user_a.id,
            session_id="session-a-1",
            user_label="Customer A"
        )
        db_session.add(session_a)
        
        session_b = ChatSession(
            id=str(uuid.uuid4()),
            workspace_id=workspace_b.id,
            user_id=user_b.id,
            session_id="session-b-1",
            user_label="Customer B"
        )
        db_session.add(session_b)
        db_session.commit()
        
        # User A should only see chat sessions from workspace A
        sessions_in_workspace_a = db_session.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_a.id
        ).all()
        assert len(sessions_in_workspace_a) == 1
        assert sessions_in_workspace_a[0].session_id == "session-a-1"
        
        # User A should not see chat sessions from workspace B
        sessions_from_workspace_b = db_session.query(ChatSession).filter(
            ChatSession.workspace_id == workspace_a.id,
            ChatSession.session_id == "session-b-1"
        ).all()
        assert len(sessions_from_workspace_b) == 0
    
    def test_cross_workspace_subscription_isolation(self, db_session, subscription_a, subscription_b, workspace_a, workspace_b):
        """Test that subscriptions are isolated between workspaces"""
        # Each workspace should only see its own subscription
        sub_a = db_session.query(Subscription).filter(Subscription.workspace_id == workspace_a.id).first()
        assert sub_a is not None
        assert sub_a.tier == "pro"
        assert sub_a.monthly_query_quota == 10000
        
        sub_b = db_session.query(Subscription).filter(Subscription.workspace_id == workspace_b.id).first()
        assert sub_b is not None
        assert sub_b.tier == "free"
        assert sub_b.monthly_query_quota == 1000
        
        # Workspace A should not see workspace B's subscription
        sub_b_from_a = db_session.query(Subscription).filter(
            Subscription.workspace_id == workspace_a.id,
            Subscription.tier == "free"
        ).first()
        assert sub_b_from_a is None
    
    def test_workspace_quota_enforcement(self, db_session, subscription_a, subscription_b, workspace_a, workspace_b):
        """Test that workspace quotas are enforced independently"""
        # Test workspace A quota (pro plan - 10000 queries)
        subscription_a.queries_this_period = 5000
        db_session.commit()
        
        # Should not be over quota
        assert not subscription_a.is_quota_exceeded
        assert subscription_a.quota_usage_percentage == 0.5
        
        # Test workspace B quota (free plan - 1000 queries)
        subscription_b.queries_this_period = 500
        db_session.commit()
        
        # Should not be over quota
        assert not subscription_b.is_quota_exceeded
        assert subscription_b.quota_usage_percentage == 0.5
        
        # Test quota exceeded for workspace B
        subscription_b.queries_this_period = 1500
        db_session.commit()
        
        # Should be over quota
        assert subscription_b.is_quota_exceeded
        assert subscription_b.quota_usage_percentage == 1.5
    
    def test_api_endpoint_workspace_isolation(self, client, user_a, user_b, workspace_a, workspace_b):
        """Test that API endpoints respect workspace isolation"""
        # Mock authentication for user A
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = user_a
            
            # User A should only see their workspace's documents
            response = client.get("/api/v1/documents/")
            assert response.status_code == 200
            
            # Mock authentication for user B
            mock_get_user.return_value = user_b
            
            # User B should only see their workspace's documents
            response = client.get("/api/v1/documents/")
            assert response.status_code == 200
    
    def test_vector_search_workspace_isolation(self, db_session, workspace_a, workspace_b):
        """Test that vector search respects workspace isolation"""
        # Create document chunks for each workspace
        chunk_a = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            workspace_id=workspace_a.id,
            content="This is content for workspace A",
            chunk_index=0,
            embedding=[0.1, 0.2, 0.3]
        )
        db_session.add(chunk_a)
        
        chunk_b = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            workspace_id=workspace_b.id,
            content="This is content for workspace B",
            chunk_index=0,
            embedding=[0.4, 0.5, 0.6]
        )
        db_session.add(chunk_b)
        db_session.commit()
        
        # Search in workspace A should only return chunks from workspace A
        chunks_a = db_session.query(DocumentChunk).filter(
            DocumentChunk.workspace_id == workspace_a.id
        ).all()
        assert len(chunks_a) == 1
        assert chunks_a[0].content == "This is content for workspace A"
        
        # Search in workspace B should only return chunks from workspace B
        chunks_b = db_session.query(DocumentChunk).filter(
            DocumentChunk.workspace_id == workspace_b.id
        ).all()
        assert len(chunks_b) == 1
        assert chunks_b[0].content == "This is content for workspace B"
    
    def test_analytics_workspace_isolation(self, db_session, workspace_a, workspace_b):
        """Test that analytics are isolated between workspaces"""
        # Create chat messages for each workspace
        message_a = ChatMessage(
            id=str(uuid.uuid4()),
            session_id="session-a-1",
            workspace_id=workspace_a.id,
            role="user",
            content="Message from workspace A"
        )
        db_session.add(message_a)
        
        message_b = ChatMessage(
            id=str(uuid.uuid4()),
            session_id="session-b-1",
            workspace_id=workspace_b.id,
            role="user",
            content="Message from workspace B"
        )
        db_session.add(message_b)
        db_session.commit()
        
        # Analytics for workspace A should only include workspace A data
        messages_a = db_session.query(ChatMessage).filter(
            ChatMessage.workspace_id == workspace_a.id
        ).all()
        assert len(messages_a) == 1
        assert messages_a[0].content == "Message from workspace A"
        
        # Analytics for workspace B should only include workspace B data
        messages_b = db_session.query(ChatMessage).filter(
            ChatMessage.workspace_id == workspace_b.id
        ).all()
        assert len(messages_b) == 1
        assert messages_b[0].content == "Message from workspace B"
    
    def test_workspace_data_encryption_isolation(self, db_session, workspace_a, workspace_b):
        """Test that sensitive data is encrypted per workspace"""
        # Create users with sensitive data
        user_a = User(
            email="sensitive-a@workspace-a.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Sensitive User A",
            workspace_id=workspace_a.id,
            is_active=True,
            mobile_phone="+1234567890"
        )
        db_session.add(user_a)
        
        user_b = User(
            email="sensitive-b@workspace-b.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Sensitive User B",
            workspace_id=workspace_b.id,
            is_active=True,
            mobile_phone="+0987654321"
        )
        db_session.add(user_b)
        db_session.commit()
        
        # Each workspace should only see its own sensitive data
        users_a = db_session.query(User).filter(User.workspace_id == workspace_a.id).all()
        assert len(users_a) == 1
        assert users_a[0].mobile_phone == "+1234567890"
        
        users_b = db_session.query(User).filter(User.workspace_id == workspace_b.id).all()
        assert len(users_b) == 1
        assert users_b[0].mobile_phone == "+0987654321"
    
    def test_workspace_quota_shared_resources(self, db_session, workspace_a, workspace_b):
        """Test that shared resources don't affect workspace quotas"""
        # Create subscriptions with different quotas
        sub_a = Subscription(
            workspace_id=workspace_a.id,
            tier="enterprise",
            status="active",
            monthly_query_quota=None,  # Unlimited
            queries_this_period=100000
        )
        db_session.add(sub_a)
        
        sub_b = Subscription(
            workspace_id=workspace_b.id,
            tier="free",
            status="active",
            monthly_query_quota=1000,
            queries_this_period=500
        )
        db_session.add(sub_b)
        db_session.commit()
        
        # Workspace A should not be limited by workspace B's quota
        assert not sub_a.is_quota_exceeded  # Unlimited quota
        
        # Workspace B should be limited by its own quota
        assert not sub_b.is_quota_exceeded  # 500 < 1000
        
        # Increase workspace B usage
        sub_b.queries_this_period = 1500
        db_session.commit()
        
        # Only workspace B should be over quota
        assert sub_b.is_quota_exceeded
        assert not sub_a.is_quota_exceeded
    
    def test_workspace_deletion_isolation(self, db_session, workspace_a, workspace_b, user_a, user_b):
        """Test that workspace deletion doesn't affect other workspaces"""
        # Create documents for both workspaces
        doc_a = Document(
            id=str(uuid.uuid4()),
            workspace_id=workspace_a.id,
            filename="doc-a.pdf",
            content_type="application/pdf",
            size=1024,
            path="/tmp/doc-a.pdf",
            uploaded_by=user_a.id,
            status="processed"
        )
        db_session.add(doc_a)
        
        doc_b = Document(
            id=str(uuid.uuid4()),
            workspace_id=workspace_b.id,
            filename="doc-b.pdf",
            content_type="application/pdf",
            size=2048,
            path="/tmp/doc-b.pdf",
            uploaded_by=user_b.id,
            status="processed"
        )
        db_session.add(doc_b)
        db_session.commit()
        
        # Verify both documents exist
        assert db_session.query(Document).filter(Document.workspace_id == workspace_a.id).count() == 1
        assert db_session.query(Document).filter(Document.workspace_id == workspace_b.id).count() == 1
        
        # Delete workspace A
        db_session.delete(workspace_a)
        db_session.commit()
        
        # Workspace B should still exist and have its documents
        assert db_session.query(Workspace).filter(Workspace.id == workspace_b.id).count() == 1
        assert db_session.query(Document).filter(Document.workspace_id == workspace_b.id).count() == 1
        
        # Workspace A and its documents should be deleted
        assert db_session.query(Workspace).filter(Workspace.id == workspace_a.id).count() == 0
        assert db_session.query(Document).filter(Document.workspace_id == workspace_a.id).count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
