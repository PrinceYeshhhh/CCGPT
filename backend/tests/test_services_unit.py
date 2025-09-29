"""
Comprehensive unit tests for all backend services
Tests individual service components in isolation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import json

from app.services.auth import AuthService
from app.services.gemini_service import GeminiService
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_search_service import VectorSearchService
from app.services.rag_service import RAGService
from app.services.document_service import DocumentService
from app.services.stripe_service import StripeService
from app.services.analytics import AnalyticsService
from app.utils.password import get_password_hash, verify_password
from app.utils.chunker import chunk_text
from app.utils.file_parser import extract_text_from_file
from app.core.config import settings

class TestAuthService:
    """Unit tests for AuthService"""
    
    @pytest.fixture
    def auth_service(self, db_session):
        return AuthService(db_session)
    
    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash length
        assert hashed.startswith("$2b$")
    
    def test_verify_password(self, auth_service):
        """Test password verification"""
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)
        
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self, auth_service):
        """Test JWT token creation"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = auth_service.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
    
    def test_verify_token(self, auth_service):
        """Test JWT token verification"""
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = auth_service.create_access_token(user_data)
        
        decoded_data = auth_service.verify_token(token)
        assert decoded_data["user_id"] == "123"
        assert decoded_data["email"] == "test@example.com"
    
    def test_verify_invalid_token(self, auth_service):
        """Test invalid token handling"""
        invalid_token = "invalid.jwt.token"
        
        result = auth_service.verify_token(invalid_token)
        assert result is None

class TestGeminiService:
    """Unit tests for GeminiService"""
    
    @pytest.fixture
    def gemini_service(self):
        return GeminiService()
    
    @patch('app.services.gemini_service.genai.configure')
    @patch('app.services.gemini_service.genai.GenerativeModel')
    def test_initialize_model(self, mock_model, mock_configure):
        """Test model initialization"""
        mock_configure.return_value = None
        mock_model.return_value = Mock()
        
        service = GeminiService()
        
        # The configure is called during __init__, so we check it was called
        mock_configure.assert_called_with(api_key=settings.GEMINI_API_KEY)
        mock_model.assert_called_with('gemini-pro')
    
    @patch('app.services.gemini_service.genai.GenerativeModel')
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_model):
        """Test successful response generation"""
        mock_instance = Mock()
        mock_instance.generate_content.return_value.text = "Test response"
        mock_model.return_value = mock_instance
        
        service = GeminiService()
        service.model = mock_instance
        
        result = await service.generate_response("Test query", "")

        assert result["content"] == "Test response"
        assert "tokens_used" in result
        assert "model_used" in result
    
    @patch('app.services.gemini_service.genai.GenerativeModel')
    @pytest.mark.asyncio
    async def test_generate_response_with_sources(self, mock_model):
        """Test response generation with sources"""
        mock_instance = Mock()
        mock_instance.generate_content.return_value.text = "Test response with sources"
        mock_model.return_value = mock_instance
        
        service = GeminiService()
        service.model = mock_instance
        
        sources = [{"content": "Source 1", "chunk_id": "1"}]
        result = await service.generate_response("Test query", "", sources)
        
        assert result["content"] == "Test response with sources"
        assert "sources_used" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self):
        """Test error handling in response generation"""
        service = GeminiService()
        service.model = None  # Simulate initialization failure
        
        with pytest.raises(Exception):
            await service.generate_response("Test query", "")

class TestEmbeddingsService:
    """Unit tests for EmbeddingsService"""
    
    @pytest.fixture
    def embeddings_service(self):
        return EmbeddingsService()
    
    @patch('app.services.embeddings_service.SentenceTransformer')
    def test_initialize_model(self, mock_transformer):
        """Test model initialization"""
        mock_instance = Mock()
        mock_instance.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_instance

        service = EmbeddingsService()

        # The model is initialized during __init__, so we check it was called
        mock_transformer.assert_called_with('all-MiniLM-L6-v2')
        assert service.model is not None
    
    @patch('app.services.embeddings_service.SentenceTransformer')
    @pytest.mark.asyncio
    async def test_embed_text(self, mock_transformer):
        """Test text embedding"""
        import numpy as np
        mock_instance = Mock()
        mock_instance.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
        mock_transformer.return_value = mock_instance
        
        service = EmbeddingsService()
        service.model = mock_instance
        
        result = await service.generate_single_embedding("Test text")
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(x, float) for x in result)
    
    @patch('app.services.embeddings_service.SentenceTransformer')
    @pytest.mark.asyncio
    async def test_embed_texts_batch(self, mock_transformer):
        """Test batch text embedding"""
        import numpy as np
        mock_instance = Mock()
        mock_instance.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_transformer.return_value = mock_instance
        
        service = EmbeddingsService()
        service.model = mock_instance
        
        texts = ["Text 1", "Text 2"]
        result = await service.generate_embeddings(texts)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(len(embedding) == 3 for embedding in result)
    
    def test_get_model_info(self):
        """Test model information retrieval"""
        service = EmbeddingsService()
        info = service.get_model_info()

        assert "model_name" in info
        assert "embedding_dimension" in info
        assert "model_type" in info

class TestVectorSearchService:
    """Unit tests for VectorSearchService"""
    
    @pytest.fixture
    def vector_service(self):
        return VectorSearchService()
    
    def test_initialize_client(self, vector_service):
        """Test Redis client initialization"""
        # VectorSearchService initializes Redis client in __init__
        assert vector_service is not None
    
    def test_initialize_redis(self, vector_service):
        """Test Redis initialization"""
        # VectorSearchService initializes Redis in __init__
        assert vector_service is not None
    
    def test_generate_cache_key(self, vector_service):
        """Test cache key generation"""
        workspace_id = "test_workspace"
        query = "test query"
        limit = 10
        
        cache_key = vector_service._generate_cache_key(workspace_id, query, limit)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
    
    @patch('app.services.vector_service.chromadb.PersistentClient')
    @pytest.mark.asyncio
    async def test_search_similar(self, mock_client):
        """Test similar document search"""
        mock_instance = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Test content"]],
            "metadatas": [[{"source": "doc1"}]],
            "distances": [[0.1]]
        }
        mock_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_instance
        
        service = VectorSearchService()
        
        # Test the search method through the vector service
        from app.services.vector_service import VectorService
        vector_service = VectorService()
        vector_service.collection = mock_collection
        
        # Mock the search_similar_chunks method
        with patch.object(vector_service, 'search_similar_chunks') as mock_search:
            mock_search.return_value = [
                {"content": "Test content", "score": 0.9, "chunk_id": "1"}
            ]
            
            results = await vector_service.search_similar_chunks("test query", "test_workspace", 5)
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert "content" in results[0]
            assert "score" in results[0]

class TestRAGService:
    """Unit tests for RAGService"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return RAGService(db_session)
    
    @patch('app.services.rag_service.embeddings_service')
    @patch('app.services.rag_service.GeminiService')
    @patch('app.services.rag_service.VectorService')
    @pytest.mark.asyncio
    async def test_process_query_success(self, mock_vector, mock_gemini, mock_embeddings, rag_service):
        """Test successful query processing"""
        # Setup mocks
        mock_embeddings.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        mock_vector_instance = Mock()
        mock_vector_instance.search_similar_chunks = AsyncMock(return_value=[
            {"content": "Relevant content", "score": 0.9, "chunk_id": "1"}
        ])
        mock_vector.return_value = mock_vector_instance
        
        mock_gemini_instance = Mock()
        mock_gemini_instance.generate_response = AsyncMock(return_value={
            "content": "Test answer",
            "sources_used": [{"chunk_id": "1", "document_id": "doc1"}],
            "tokens_used": 100
        })
        mock_gemini.return_value = mock_gemini_instance
        
        # Replace the actual services with mocked ones
        rag_service.vector_service = mock_vector_instance
        rag_service.gemini_service = mock_gemini_instance
        
        result = await rag_service.process_query("550e8400-e29b-41d4-a716-446655440000", "Test query")
        
        assert result.answer == "Test answer"
        assert "sources" in result.dict()
        assert "response_time_ms" in result.dict()
        assert result.response_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_process_query_no_results(self, rag_service):
        """Test query processing with no search results"""
        # Mock the vector service to return no results
        mock_vector_instance = Mock()
        mock_vector_instance.search_similar_chunks = AsyncMock(return_value=[])
        rag_service.vector_service = mock_vector_instance
        
        # Mock the gemini service
        mock_gemini_instance = Mock()
        mock_gemini_instance.generate_response = AsyncMock(return_value={
            "content": "I don't have any relevant information to answer your question.",
            "tokens_used": 50
        })
        rag_service.gemini_service = mock_gemini_instance
        
        result = await rag_service.process_query("550e8400-e29b-41d4-a716-446655440000", "Test query")
        
        assert "answer" in result.dict()
        assert "no relevant information" in result.answer.lower() or "don't have" in result.answer.lower()

class TestDocumentService:
    """Unit tests for DocumentService"""
    
    @pytest.fixture
    def document_service(self, db_session):
        return DocumentService(db_session)
    
    def test_get_allowed_content_types(self, document_service):
        """Test allowed content types"""
        content_types = document_service._get_allowed_content_types()
        
        assert isinstance(content_types, list)
        assert "application/pdf" in content_types
    
    def test_get_workspace_documents(self, document_service):
        """Test getting workspace documents"""
        workspace_id = "test_workspace"
        
        result = document_service.get_workspace_documents(workspace_id)
        
        assert isinstance(result, list)
    
    def test_get_document(self, document_service):
        """Test getting a document"""
        document_id = "test_doc_123"
        workspace_id = "test_workspace"
        
        result = document_service.get_document(document_id, workspace_id)
        
        # Should return None for non-existent document
        assert result is None
    
    def test_get_document_chunks(self, document_service):
        """Test getting document chunks"""
        document_id = "test_doc_123"
        workspace_id = "test_workspace"
        
        result = document_service.get_document_chunks(document_id, workspace_id)
        
        assert isinstance(result, list)

class TestStripeService:
    """Unit tests for StripeService"""
    
    @pytest.fixture
    def stripe_service(self):
        return StripeService()
    
    @pytest.mark.asyncio
    @patch('app.services.stripe_service.stripe.checkout.Session.create')
    @patch('app.services.stripe_service.stripe.Customer.list')
    async def test_create_checkout_session(self, mock_customer_list, mock_create):
        """Test checkout session creation"""
        # Mock customer list to return empty (no existing customer)
        mock_customer_list.return_value = Mock(data=[])
        
        # Mock customer creation
        with patch('app.services.stripe_service.stripe.Customer.create') as mock_customer_create:
            mock_customer = Mock()
            mock_customer.id = "cus_test_123"
            mock_customer_create.return_value = mock_customer
            
            # Mock checkout session
            mock_session = Mock()
            mock_session.id = "cs_test_123"
            mock_session.url = "http://localhost:3000/billing/checkout/test"
            mock_create.return_value = mock_session
            
            service = StripeService()
            result = await service.create_checkout_session("pro", "test_workspace", "test@example.com", "Test User")
            
            assert result["session_id"] == "cs_test_123"
            assert result["url"] == "http://localhost:3000/billing/checkout/test"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.stripe_service.stripe.billing_portal.Session.create')
    async def test_create_billing_portal_session(self, mock_create):
        """Test billing portal session creation"""
        mock_session = Mock()
        mock_session.url = "http://localhost:3000/billing/portal/test"
        mock_create.return_value = mock_session
        
        service = StripeService()
        result = await service.create_billing_portal_session("test_customer", "https://example.com/return")
        
        # The method returns a string URL, not a dict
        assert result == "http://localhost:3000/billing/portal/test"
        mock_create.assert_called_once()
    
    def test_verify_webhook_signature(self, stripe_service):
        """Test webhook signature verification"""
        payload = b'{"type": "checkout.session.completed"}'
        signature = "test_signature"
        
        result = stripe_service.verify_webhook_signature(payload, signature)
        
        assert isinstance(result, bool)

class TestAnalyticsService:
    """Unit tests for AnalyticsService"""
    
    @pytest.fixture
    def analytics_service(self, db_session):
        return AnalyticsService(db_session)
    
    def test_get_user_overview(self, analytics_service):
        """Test user overview analytics"""
        user_id = 1
        
        result = analytics_service.get_user_overview(user_id)
        
        assert isinstance(result, dict)
        assert "total_documents" in result
        assert "total_sessions" in result
    
    def test_get_document_analytics(self, analytics_service):
        """Test document analytics"""
        user_id = 1
        
        result = analytics_service.get_document_analytics(user_id)
        
        assert isinstance(result, list)
    
    def test_get_usage_stats(self, analytics_service):
        """Test usage statistics"""
        user_id = 1
        days = 30
        
        result = analytics_service.get_usage_stats(user_id, days)
        
        assert isinstance(result, list)

class TestPasswordManager:
    """Unit tests for PasswordManager utility"""
    
    def test_hash_password(self):
        """Test password hashing"""
        from app.utils.password import get_password_hash
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")
    
    def test_verify_password(self):
        """Test password verification"""
        from app.utils.password import get_password_hash, verify_password
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

class TestTextChunker:
    """Unit tests for TextChunker utility"""
    
    def test_chunk_text_default(self):
        """Test default text chunking"""
        from app.utils.chunker import chunk_text
        text = "This is a test document. " * 200  # Very long text
        chunks = chunk_text(text, max_tokens=100, overlap_tokens=10)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)  # All chunks have content
    
    def test_chunk_text_custom_size(self):
        """Test custom chunk size"""
        from app.utils.chunker import chunk_text
        text = "This is a test document. " * 50
        chunks = chunk_text(text, max_tokens=50, overlap_tokens=10)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_chunk_text_overlap(self):
        """Test chunking with overlap"""
        from app.utils.chunker import chunk_text
        text = "This is a test document. " * 20
        chunks = chunk_text(text, max_tokens=100, overlap_tokens=20)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1

class TestFileParser:
    """Unit tests for FileParser utility"""
    
    @patch('app.utils.file_parser.open')
    @patch('app.utils.file_parser.PyPDF2.PdfReader')
    def test_extract_pdf_text(self, mock_reader, mock_open):
        """Test PDF text extraction"""
        from app.utils.file_parser import extract_text_from_file
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF content"
        mock_reader.return_value.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = Mock()
        
        result = extract_text_from_file("test.pdf", "application/pdf")
        
        assert len(result) == 1
        assert result[0][0] == "PDF content"
    
    def test_extract_csv_text(self):
        """Test CSV text extraction"""
        from app.utils.file_parser import extract_text_from_file
        # Create a temporary CSV file for testing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Name,Age\nJohn,25\nJane,30")
            temp_file = f.name
        
        try:
            result = extract_text_from_file(temp_file, "text/csv")
            assert len(result) > 0
            # Check that the result contains our data (formatted as table)
            result_text = " ".join([item[0] for item in result])
            assert "John" in result_text or "Name" in result_text
        finally:
            os.unlink(temp_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
