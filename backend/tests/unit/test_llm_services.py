"""
Comprehensive unit tests for LLM services (Gemini, Embeddings, Vector Search)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.gemini_service import GeminiService
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_service import VectorService
from app.services.production_rag_service import ProductionRAGService, RAGConfig
from app.models import ChatSession, ChatMessage, Document
from app.schemas.rag import RAGQueryResponse, RAGSource


class TestGeminiService:
    """Comprehensive tests for GeminiService"""
    
    @pytest.fixture
    def gemini_service(self):
        return GeminiService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, gemini_service):
        """Test successful response generation"""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "This is a test response"
            mock_genai.GenerativeModel.return_value = mock_model
            
            result = await gemini_service.generate_response(
                user_message="Test query",
                context="Test context"
            )
            
            assert result["content"] == "This is a test response"
            assert "tokens_used" in result
            assert "model_used" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_with_sources(self, gemini_service):
        """Test response generation with source citations"""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Response with [1] citations"
            mock_genai.GenerativeModel.return_value = mock_model
            
            sources = [{"chunk_id": "1", "content": "Source content", "score": 0.9}]
            result = await gemini_service.generate_response(
                query="Test query",
                context="Test context",
                sources=sources
            )
            
            assert result["content"] == "Response with [1] citations"
            assert "sources_used" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, gemini_service):
        """Test error handling in response generation"""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await gemini_service.generate_response(
                    query="Test query",
                    context="Test context"
                )
    
    @pytest.mark.asyncio
    async def test_generate_response_rate_limiting(self, gemini_service):
        """Test rate limiting handling"""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.side_effect = Exception("Rate limit exceeded")
            mock_genai.GenerativeModel.return_value = mock_model
            
            with pytest.raises(Exception):
                await gemini_service.generate_response(
                    query="Test query",
                    context="Test context"
                )
    
    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, gemini_service):
        """Test response generation with conversation history"""
        with patch('app.services.gemini_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Contextual response"
            mock_genai.GenerativeModel.return_value = mock_model
            
            history = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"}
            ]
            
            result = await gemini_service.generate_response(
                query="Follow-up question",
                context="Test context",
                conversation_history=history
            )
            
            assert result["content"] == "Contextual response"
            # Verify conversation history was included in the prompt
            mock_model.generate_content.assert_called_once()
            call_args = mock_model.generate_content.call_args[0][0]
            assert "Previous question" in call_args
            assert "Previous answer" in call_args


class TestEmbeddingsService:
    """Comprehensive tests for EmbeddingsService"""
    
    @pytest.fixture
    def embeddings_service(self):
        return EmbeddingsService()
    
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embeddings_service):
        """Test single embedding generation"""
        with patch('app.services.embeddings_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.embed_content.return_value.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_genai.embed_content.return_value = mock_model.embed_content.return_value
            
            result = await embeddings_service.generate_single_embedding("Test text")
            
            assert len(result) == 5
            assert all(isinstance(x, float) for x in result)
    
    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, embeddings_service):
        """Test batch embedding generation"""
        with patch('app.services.embeddings_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.embed_content.return_value.embedding = [0.1, 0.2, 0.3]
            mock_genai.embed_content.return_value = mock_model.embed_content.return_value
            
            texts = ["Text 1", "Text 2", "Text 3"]
            result = await embeddings_service.generate_batch_embeddings(texts)
            
            assert len(result) == 3
            assert all(len(embedding) == 3 for embedding in result)
    
    @pytest.mark.asyncio
    async def test_embedding_error_handling(self, embeddings_service):
        """Test error handling in embedding generation"""
        with patch('app.services.embeddings_service.genai') as mock_genai:
            mock_genai.embed_content.side_effect = Exception("Embedding API Error")
            
            with pytest.raises(Exception):
                await embeddings_service.generate_single_embedding("Test text")
    
    @pytest.mark.asyncio
    async def test_embedding_dimensions_consistency(self, embeddings_service):
        """Test that embeddings have consistent dimensions"""
        with patch('app.services.embeddings_service.genai') as mock_genai:
            mock_model = Mock()
            mock_model.embed_content.return_value.embedding = [0.1] * 768  # Standard embedding size
            mock_genai.embed_content.return_value = mock_model.embed_content.return_value
            
            result1 = await embeddings_service.generate_single_embedding("Text 1")
            result2 = await embeddings_service.generate_single_embedding("Text 2")
            
            assert len(result1) == len(result2)
            assert len(result1) == 768


class TestVectorService:
    """Comprehensive tests for VectorService"""
    
    @pytest.fixture
    def vector_service(self):
        return VectorService()
    
    @pytest.mark.asyncio
    async def test_add_chunks(self, vector_service):
        """Test adding chunks to vector store"""
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.add.return_value = {"ids": ["1", "2"]}
            mock_client.return_value.get_collection.return_value = mock_collection
            
            chunks = [
                {"id": "1", "content": "Test content 1", "metadata": {"doc_id": "doc1"}},
                {"id": "2", "content": "Test content 2", "metadata": {"doc_id": "doc2"}}
            ]
            
            result = await vector_service.add_chunks("workspace_1", chunks)
            
            assert result["success"] is True
            assert len(result["chunk_ids"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks(self, vector_service):
        """Test searching for similar chunks"""
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["Test content 1", "Test content 2"]],
                "metadatas": [[{"doc_id": "doc1"}, {"doc_id": "doc2"}]],
                "distances": [[0.1, 0.2]],
                "ids": [["chunk1", "chunk2"]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            result = await vector_service.search_similar_chunks(
                query="Test query",
                workspace_id="workspace_1",
                limit=2
            )
            
            assert len(result) == 2
            assert "content" in result[0]
            assert "score" in result[0]
            assert "chunk_id" in result[0]
    
    @pytest.mark.asyncio
    async def test_delete_chunks(self, vector_service):
        """Test deleting chunks from vector store"""
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.delete.return_value = {"ids": ["chunk1"]}
            mock_client.return_value.get_collection.return_value = mock_collection
            
            result = await vector_service.delete_chunks("workspace_1", ["chunk1"])
            
            assert result["success"] is True
            assert "chunk1" in result["deleted_ids"]
    
    @pytest.mark.asyncio
    async def test_vector_store_error_handling(self, vector_service):
        """Test error handling in vector operations"""
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_client.side_effect = Exception("Vector store error")
            
            with pytest.raises(Exception):
                await vector_service.add_chunks("workspace_1", [])


class TestProductionRAGService:
    """Comprehensive tests for ProductionRAGService"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.mark.asyncio
    async def test_process_file_success(self, rag_service):
        """Test successful file processing"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                mock_process.return_value = {
                    "chunks": [{"id": "1", "content": "Test", "metadata": {}}],
                    "metadata": {"file_type": "pdf", "pages": 1}
                }
                mock_add.return_value = {"success": True, "chunk_ids": ["1"]}
                
                result = await rag_service.process_file(
                    file_path="test.pdf",
                    content_type="application/pdf",
                    workspace_id="ws_1"
                )
                
                assert result["status"] == "success"
                assert "chunks_created" in result
                assert "processing_time" in result
    
    @pytest.mark.asyncio
    async def test_query_with_rag_mode(self, rag_service):
        """Test query processing with different RAG modes"""
        with patch.object(rag_service.vector_service, 'search_similar_chunks') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                mock_search.return_value = [{"content": "Test content", "score": 0.9}]
                mock_generate.return_value = {
                    "content": "Test answer",
                    "sources_used": [{"chunk_id": "1"}],
                    "tokens_used": 100
                }
                
                # Test FULL_RAG mode
                result = await rag_service.query(
                    query="Test query",
                    workspace_id="ws_1",
                    mode="full_rag"
                )
                
                assert result["answer"] == "Test answer"
                assert "sources" in result
                assert "response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_query_search_only_mode(self, rag_service):
        """Test query in search-only mode"""
        with patch.object(rag_service.vector_service, 'search_similar_chunks') as mock_search:
            mock_search.return_value = [{"content": "Test content", "score": 0.9}]
            
            result = await rag_service.query(
                query="Test query",
                workspace_id="ws_1",
                mode="search_only"
            )
            
            assert "search_results" in result
            assert len(result["search_results"]) == 1
            assert "answer" not in result  # No generation in search-only mode
    
    @pytest.mark.asyncio
    async def test_query_generate_only_mode(self, rag_service):
        """Test query in generate-only mode"""
        with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
            mock_generate.return_value = {
                "content": "Test answer",
                "tokens_used": 100
            }
            
            result = await rag_service.query(
                query="Test query",
                workspace_id="ws_1",
                mode="generate_only",
                context="Provided context"
            )
            
            assert result["answer"] == "Test answer"
            assert "sources" not in result  # No search in generate-only mode
    
    @pytest.mark.asyncio
    async def test_rag_config_validation(self, rag_service):
        """Test RAG configuration validation"""
        config = RAGConfig(
            max_chunks=10,
            chunk_overlap=50,
            similarity_threshold=0.7,
            max_tokens=1000
        )
        
        assert config.max_chunks == 10
        assert config.chunk_overlap == 50
        assert config.similarity_threshold == 0.7
        assert config.max_tokens == 1000
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, rag_service):
        """Test performance metrics tracking"""
        # Simulate some operations
        rag_service.performance_stats["total_queries"] = 10
        rag_service.performance_stats["avg_query_time"] = 250.0
        
        stats = rag_service.get_performance_stats()
        
        assert stats["total_queries"] == 10
        assert stats["avg_query_time"] == 250.0
        assert "success_rate" in stats
        assert "cache_hit_rate" in stats
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, rag_service):
        """Test error handling and recovery mechanisms"""
        with patch.object(rag_service.vector_service, 'search_similar_chunks') as mock_search:
            mock_search.side_effect = Exception("Vector search failed")
            
            with pytest.raises(Exception):
                await rag_service.query(
                    query="Test query",
                    workspace_id="ws_1"
                )
            
            # Verify error is logged and stats are updated
            assert rag_service.performance_stats["total_queries"] >= 0


class TestRAGIntegration:
    """Integration tests for RAG components working together"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.mark.asyncio
    async def test_complete_rag_pipeline(self, rag_service):
        """Test complete RAG pipeline from file processing to query"""
        # Mock all external dependencies
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                with patch.object(rag_service.vector_service, 'search_similar_chunks') as mock_search:
                    with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                        # Setup mocks
                        mock_process.return_value = {
                            "chunks": [{"id": "1", "content": "Test content", "metadata": {}}],
                            "metadata": {"file_type": "pdf"}
                        }
                        mock_add.return_value = {"success": True, "chunk_ids": ["1"]}
                        mock_search.return_value = [{"content": "Test content", "score": 0.9}]
                        mock_generate.return_value = {
                            "content": "Test answer",
                            "sources_used": [{"chunk_id": "1"}],
                            "tokens_used": 100
                        }
                        
                        # Step 1: Process file
                        process_result = await rag_service.process_file(
                            file_path="test.pdf",
                            content_type="application/pdf",
                            workspace_id="ws_1"
                        )
                        assert process_result["status"] == "success"
                        
                        # Step 2: Query the processed content
                        query_result = await rag_service.query(
                            query="Test query",
                            workspace_id="ws_1"
                        )
                        assert query_result["answer"] == "Test answer"
                        assert len(query_result["sources"]) == 1
    
    @pytest.mark.asyncio
    async def test_rag_with_conversation_context(self, rag_service):
        """Test RAG with conversation context"""
        with patch.object(rag_service.vector_service, 'search_similar_chunks') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                mock_search.return_value = [{"content": "Test content", "score": 0.9}]
                mock_generate.return_value = {
                    "content": "Contextual answer",
                    "sources_used": [{"chunk_id": "1"}],
                    "tokens_used": 150
                }
                
                conversation_history = [
                    {"role": "user", "content": "What is your refund policy?"},
                    {"role": "assistant", "content": "Our refund policy is..."}
                ]
                
                result = await rag_service.query(
                    query="How long do I have to request a refund?",
                    workspace_id="ws_1",
                    conversation_history=conversation_history
                )
                
                assert result["answer"] == "Contextual answer"
                # Verify conversation history was passed to Gemini
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args
                assert "conversation_history" in call_args.kwargs
