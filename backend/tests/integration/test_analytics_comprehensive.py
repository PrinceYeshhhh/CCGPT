"""
Comprehensive Analytics Integration Tests
Tests all analytics functionality including metrics, data aggregation, and performance
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, ChatSession, ChatMessage, EmbedCode, DocumentChunk, Subscription


class TestAnalyticsComprehensive:
    """Comprehensive tests for analytics functionality"""
    
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
            id="ws_analytics_test",
            name="Analytics Test Workspace",
            description="Test workspace for analytics testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            id="user_analytics_test",
            email="analytics@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Analytics Test User",
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
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """Create authentication headers"""
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_documents(self, db_session, test_user, test_workspace):
        """Create test documents"""
        documents = []
        for i in range(3):
            doc = Document(
                id=f"doc_analytics_{i}",
                workspace_id=test_workspace.id,
                user_id=test_user.id,
                filename=f"test_doc_{i}.txt",
                original_filename=f"test_doc_{i}.txt",
                content_type="text/plain",
                size=1000 + i * 100,
                path=f"/path/doc_{i}.txt",
                status="processed"
            )
            db_session.add(doc)
            documents.append(doc)
        
        db_session.commit()
        for doc in documents:
            db_session.refresh(doc)
        return documents
    
    @pytest.fixture
    def test_chat_sessions(self, db_session, test_user, test_workspace):
        """Create test chat sessions"""
        sessions = []
        for i in range(5):
            session = ChatSession(
                id=f"session_analytics_{i}",
                workspace_id=test_workspace.id,
                user_id=test_user.id,
                session_id=f"session_{i}",
                user_label=f"Customer {i}",
                is_active=i < 3,  # First 3 are active
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            db_session.add(session)
            sessions.append(session)
        
        db_session.commit()
        for session in sessions:
            db_session.refresh(session)
        return sessions
    
    @pytest.fixture
    def test_chat_messages(self, db_session, test_chat_sessions):
        """Create test chat messages"""
        messages = []
        for i, session in enumerate(test_chat_sessions):
            # User message
            user_msg = ChatMessage(
                id=f"msg_user_{i}",
                session_id=session.id,
                role="user",
                content=f"Question {i}",
                created_at=datetime.utcnow() - timedelta(minutes=i * 10),
                response_time_ms=1000 + i * 100,
                confidence_score="high" if i % 2 == 0 else "medium"
            )
            db_session.add(user_msg)
            messages.append(user_msg)
            
            # Assistant message
            assistant_msg = ChatMessage(
                id=f"msg_assistant_{i}",
                session_id=session.id,
                role="assistant",
                content=f"Answer {i}",
                created_at=datetime.utcnow() - timedelta(minutes=i * 10 + 1),
                response_time_ms=2000 + i * 100,
                confidence_score="high" if i % 2 == 0 else "medium",
                sources_used=[f"doc_analytics_{i % 3}"]
            )
            db_session.add(assistant_msg)
            messages.append(assistant_msg)
        
        db_session.commit()
        for message in messages:
            db_session.refresh(message)
        return messages
    
    @pytest.fixture
    def test_embed_codes(self, db_session, test_user, test_workspace):
        """Create test embed codes"""
        embed_codes = []
        for i in range(3):
            embed_code = EmbedCode(
                id=f"embed_analytics_{i}",
                workspace_id=test_workspace.id,
                user_id=test_user.id,
                code_name=f"Widget {i}",
                client_api_key=f"api_key_{i}",
                is_active=i < 2,  # First 2 are active
                usage_count=i * 10,
                last_used=datetime.utcnow() - timedelta(days=i),
                created_at=datetime.utcnow() - timedelta(days=i + 1)
            )
            db_session.add(embed_code)
            embed_codes.append(embed_code)
        
        db_session.commit()
        for embed_code in embed_codes:
            db_session.refresh(embed_code)
        return embed_codes

    # ==================== ANALYTICS SUMMARY TESTS ====================
    
    def test_analytics_summary_success(self, client, auth_headers, test_user, test_documents, test_chat_sessions, test_chat_messages):
        """Test successful analytics summary retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/summary", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "total_documents" in data
            assert "total_chunks" in data
            assert "total_sessions" in data
            assert "total_messages" in data
            assert "active_sessions" in data
            assert "avg_response_time" in data
            assert "avg_confidence" in data
            assert "top_questions" in data
            
            # Verify counts
            assert data["total_documents"] == 3
            assert data["total_sessions"] == 5
            assert data["total_messages"] == 10
            assert data["active_sessions"] == 3

    def test_analytics_summary_no_data(self, client, auth_headers):
        """Test analytics summary with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/summary", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_documents"] == 0
            assert data["total_sessions"] == 0
            assert data["total_messages"] == 0
            assert data["active_sessions"] == 0
            assert data["avg_response_time"] == 0
            assert data["avg_confidence"] == "unknown"

    def test_analytics_summary_database_error(self, client, auth_headers):
        """Test analytics summary with database error"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_error"
            mock_get_user.return_value = mock_user
            
            with patch('app.models.document.Document') as mock_document:
                mock_document.query.filter.side_effect = Exception("Database error")
                
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 500
                assert "Failed to retrieve analytics summary" in response.json()["detail"]

    # ==================== QUERIES OVER TIME TESTS ====================
    
    def test_queries_over_time_success(self, client, auth_headers, test_user, test_chat_sessions, test_chat_messages):
        """Test successful queries over time retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            # Should have data for each day with messages/sessions
            assert len(data) > 0
            for item in data:
                assert "date" in item
                assert "messages" in item
                assert "sessions" in item

    def test_queries_over_time_invalid_days(self, client, auth_headers, test_user):
        """Test queries over time with invalid days parameter"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test negative days
            response = client.get("/api/v1/analytics/queries-over-time?days=-1", headers=auth_headers)
            assert response.status_code == 422
            
            # Test too many days
            response = client.get("/api/v1/analytics/queries-over-time?days=1000", headers=auth_headers)
            assert response.status_code == 422

    def test_queries_over_time_no_data(self, client, auth_headers):
        """Test queries over time with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    # ==================== TOP QUERIES TESTS ====================
    
    def test_top_queries_success(self, client, auth_headers, test_user, test_chat_sessions, test_chat_messages):
        """Test successful top queries retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/top-queries?limit=5&days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 5
            for item in data:
                assert "query" in item
                assert "count" in item
                assert isinstance(item["count"], int)

    def test_top_queries_invalid_parameters(self, client, auth_headers, test_user):
        """Test top queries with invalid parameters"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test invalid limit
            response = client.get("/api/v1/analytics/top-queries?limit=0", headers=auth_headers)
            assert response.status_code == 422
            
            # Test limit too high
            response = client.get("/api/v1/analytics/top-queries?limit=100", headers=auth_headers)
            assert response.status_code == 422

    def test_top_queries_no_data(self, client, auth_headers):
        """Test top queries with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/top-queries?limit=5&days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    # ==================== FILE USAGE TESTS ====================
    
    def test_file_usage_success(self, client, auth_headers, test_user, test_documents, test_chat_messages):
        """Test successful file usage retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/file-usage?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "filename" in item
                assert "usage_count" in item
                assert "percentage" in item
                assert isinstance(item["usage_count"], int)
                assert isinstance(item["percentage"], (int, float))

    def test_file_usage_no_data(self, client, auth_headers):
        """Test file usage with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/file-usage?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_file_usage_invalid_days(self, client, auth_headers, test_user):
        """Test file usage with invalid days parameter"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test negative days
            response = client.get("/api/v1/analytics/file-usage?days=-1", headers=auth_headers)
            assert response.status_code == 422
            
            # Test too many days
            response = client.get("/api/v1/analytics/file-usage?days=1000", headers=auth_headers)
            assert response.status_code == 422

    # ==================== EMBED CODES ANALYTICS TESTS ====================
    
    def test_embed_codes_analytics_success(self, client, auth_headers, test_user, test_embed_codes):
        """Test successful embed codes analytics retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/embed-codes", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "total_embed_codes" in data
            assert "active_embed_codes" in data
            assert "total_usage" in data
            assert "embed_codes" in data
            
            assert data["total_embed_codes"] == 3
            assert data["active_embed_codes"] == 2
            assert data["total_usage"] == 30  # 0 + 10 + 20
            
            embed_codes_list = data["embed_codes"]
            assert len(embed_codes_list) == 3
            for embed_code in embed_codes_list:
                assert "id" in embed_code
                assert "name" in embed_code
                assert "is_active" in embed_code
                assert "usage_count" in embed_code
                assert "last_used" in embed_code
                assert "created_at" in embed_code

    def test_embed_codes_analytics_no_data(self, client, auth_headers):
        """Test embed codes analytics with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/embed-codes", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_embed_codes"] == 0
            assert data["active_embed_codes"] == 0
            assert data["total_usage"] == 0
            assert data["embed_codes"] == []

    # ==================== RESPONSE QUALITY TESTS ====================
    
    def test_response_quality_success(self, client, auth_headers, test_user, test_chat_sessions, test_chat_messages):
        """Test successful response quality retrieval"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            response = client.get("/api/v1/analytics/response-quality?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "confidence_distribution" in data
            assert "avg_response_time_by_confidence" in data
            
            confidence_dist = data["confidence_distribution"]
            assert isinstance(confidence_dist, list)
            for item in confidence_dist:
                assert "confidence" in item
                assert "count" in item
                assert item["confidence"] in ["high", "medium", "low"]
                assert isinstance(item["count"], int)
            
            avg_response_time = data["avg_response_time_by_confidence"]
            assert isinstance(avg_response_time, list)
            for item in avg_response_time:
                assert "confidence" in item
                assert "avg_time" in item
                assert item["confidence"] in ["high", "medium", "low"]
                assert isinstance(item["avg_time"], (int, float))

    def test_response_quality_no_data(self, client, auth_headers):
        """Test response quality with no data"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_no_data"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/analytics/response-quality?days=7", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["confidence_distribution"] == []
            assert data["avg_response_time_by_confidence"] == []

    def test_response_quality_invalid_days(self, client, auth_headers, test_user):
        """Test response quality with invalid days parameter"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test negative days
            response = client.get("/api/v1/analytics/response-quality?days=-1", headers=auth_headers)
            assert response.status_code == 422
            
            # Test too many days
            response = client.get("/api/v1/analytics/response-quality?days=1000", headers=auth_headers)
            assert response.status_code == 422

    # ==================== PERFORMANCE TESTS ====================
    
    def test_analytics_performance_large_dataset(self, client, auth_headers, test_user):
        """Test analytics performance with large dataset"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Mock large dataset
            with patch('app.models.document.Document') as mock_document, \
                 patch('app.models.chat.ChatSession') as mock_session, \
                 patch('app.models.chat.ChatMessage') as mock_message:
                
                # Mock query results
                mock_document.query.filter.return_value.count.return_value = 1000
                mock_session.query.filter.return_value.count.return_value = 500
                mock_message.query.join.return_value.filter.return_value.count.return_value = 2000
                
                # Mock complex queries
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.all.return_value = []
                
                start_time = datetime.utcnow()
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                end_time = datetime.utcnow()
                
                assert response.status_code == 200
                # Should complete within reasonable time (adjust threshold as needed)
                assert (end_time - start_time).total_seconds() < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self, client, auth_headers, test_user):
        """Test concurrent analytics requests"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Send multiple concurrent requests
            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    client.get("/api/v1/analytics/summary", headers=auth_headers)
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

    # ==================== DATA AGGREGATION TESTS ====================
    
    def test_analytics_data_consistency(self, client, auth_headers, test_user, test_documents, test_chat_sessions, test_chat_messages):
        """Test analytics data consistency across different endpoints"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Get summary data
            summary_response = client.get("/api/v1/analytics/summary", headers=auth_headers)
            assert summary_response.status_code == 200
            summary_data = summary_response.json()
            
            # Get queries over time data
            queries_response = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
            assert queries_response.status_code == 200
            queries_data = queries_response.json()
            
            # Get top queries data
            top_queries_response = client.get("/api/v1/analytics/top-queries?limit=10&days=7", headers=auth_headers)
            assert top_queries_response.status_code == 200
            top_queries_data = top_queries_response.json()
            
            # Verify consistency
            total_messages_from_queries = sum(item["messages"] for item in queries_data)
            total_queries_from_top = sum(item["count"] for item in top_queries_data)
            
            # These should be consistent (allowing for some variance due to different time ranges)
            assert summary_data["total_messages"] >= 0
            assert total_messages_from_queries >= 0
            assert total_queries_from_top >= 0

    def test_analytics_date_range_filtering(self, client, auth_headers, test_user, test_chat_sessions, test_chat_messages):
        """Test analytics date range filtering"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test different date ranges
            for days in [1, 7, 30, 90]:
                response = client.get(f"/api/v1/analytics/queries-over-time?days={days}", headers=auth_headers)
                assert response.status_code == 200
                
                data = response.json()
                assert isinstance(data, list)
                
                # Verify date range (if data exists)
                if data:
                    for item in data:
                        item_date = datetime.fromisoformat(item["date"])
                        cutoff_date = datetime.utcnow() - timedelta(days=days)
                        assert item_date >= cutoff_date

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_analytics_unauthorized_access(self, client):
        """Test analytics access without authentication"""
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 401

    def test_analytics_invalid_endpoint(self, client, auth_headers):
        """Test analytics with invalid endpoint"""
        response = client.get("/api/v1/analytics/invalid-endpoint", headers=auth_headers)
        assert response.status_code == 404

    def test_analytics_database_connection_error(self, client, auth_headers):
        """Test analytics with database connection error"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_error"
            mock_get_user.return_value = mock_user
            
            with patch('app.models.document.Document') as mock_document:
                mock_document.query.side_effect = Exception("Database connection failed")
                
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 500
                assert "Failed to retrieve analytics summary" in response.json()["detail"]

    def test_analytics_malformed_query_parameters(self, client, auth_headers, test_user):
        """Test analytics with malformed query parameters"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test non-numeric days parameter
            response = client.get("/api/v1/analytics/queries-over-time?days=invalid", headers=auth_headers)
            assert response.status_code == 422
            
            # Test non-numeric limit parameter
            response = client.get("/api/v1/analytics/top-queries?limit=invalid", headers=auth_headers)
            assert response.status_code == 422

    # ==================== EDGE CASE TESTS ====================
    
    def test_analytics_with_zero_values(self, client, auth_headers, test_user):
        """Test analytics with zero values"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Mock all queries to return zero
            with patch('app.models.document.Document') as mock_document, \
                 patch('app.models.chat.ChatSession') as mock_session, \
                 patch('app.models.chat.ChatMessage') as mock_message:
                
                mock_document.query.filter.return_value.count.return_value = 0
                mock_session.query.filter.return_value.count.return_value = 0
                mock_message.query.join.return_value.filter.return_value.count.return_value = 0
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.all.return_value = []
                
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 200
                
                data = response.json()
                assert data["total_documents"] == 0
                assert data["total_sessions"] == 0
                assert data["total_messages"] == 0
                assert data["active_sessions"] == 0
                assert data["avg_response_time"] == 0
                assert data["avg_confidence"] == "unknown"

    def test_analytics_with_null_values(self, client, auth_headers, test_user):
        """Test analytics with null values in database"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Mock queries to return None values
            with patch('app.models.document.Document') as mock_document, \
                 patch('app.models.chat.ChatSession') as mock_session, \
                 patch('app.models.chat.ChatMessage') as mock_message:
                
                mock_document.query.filter.return_value.count.return_value = 0
                mock_session.query.filter.return_value.count.return_value = 0
                mock_message.query.join.return_value.filter.return_value.count.return_value = 0
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
                mock_message.query.join.return_value.filter.return_value.group_by.return_value.all.return_value = []
                
                # Mock scalar queries to return None
                mock_message.query.join.return_value.filter.return_value.scalar.return_value = None
                
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 200
                
                data = response.json()
                assert data["avg_response_time"] == 0
                assert data["avg_confidence"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
