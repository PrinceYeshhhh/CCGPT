"""
Unit tests for Enhanced Services
Tests advanced services that are critical for production
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.services.enhanced_rag_service import (
    EnhancedRAGService,
    RetrievalStrategy,
    RerankingMethod,
    RetrievalResult,
    RerankedResult
)
from app.services.enhanced_embeddings_service import (
    EnhancedEmbeddingsService,
    EmbeddingModel
)
from app.services.enhanced_vector_service import EnhancedVectorService
from app.services.enhanced_file_processor import (
    EnhancedFileProcessor,
    ChunkingStrategy,
    TextBlock
)
from app.services.production_rag_service import (
    ProductionRAGService,
    RAGMode,
    ResponseStyle,
    RAGConfig
)
from app.services.production_vector_service import (
    ProductionVectorService,
    SearchMode,
    IndexingStrategy,
    SearchResult,
    SearchConfig
)

class TestEnhancedRAGService:
    """Unit tests for EnhancedRAGService"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return EnhancedRAGService(db_session)
    
    def test_initialization(self, rag_service):
        """Test service initialization"""
        assert rag_service is not None
        assert hasattr(rag_service, 'retrieval_strategy')
        assert hasattr(rag_service, 'reranking_method')
    
    @pytest.mark.asyncio
    async def test_process_query_with_similarity_retrieval(self, rag_service):
        """Test query processing with similarity retrieval"""
        with patch.object(rag_service, 'retrieve_similar_chunks') as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievalResult(
                    chunk_id="chunk_1",
                    content="Relevant content 1",
                    score=0.9,
                    metadata={"source": "doc1"}
                )
            ]
            
            with patch.object(rag_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "answer": "Test answer",
                    "sources": [{"chunk_id": "chunk_1"}],
                    "tokens_used": 100
                }
                
                result = await rag_service.process_query(
                    workspace_id="ws_123",
                    query="Test query",
                    retrieval_strategy=RetrievalStrategy.SIMILARITY
                )
                
                assert result is not None
                assert "answer" in result
                mock_retrieve.assert_called_once()
                mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_query_with_hybrid_retrieval(self, rag_service):
        """Test query processing with hybrid retrieval"""
        with patch.object(rag_service, 'retrieve_hybrid_chunks') as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievalResult(
                    chunk_id="chunk_1",
                    content="Relevant content 1",
                    score=0.9,
                    metadata={"source": "doc1"}
                )
            ]
            
            with patch.object(rag_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "answer": "Test answer",
                    "sources": [{"chunk_id": "chunk_1"}],
                    "tokens_used": 100
                }
                
                result = await rag_service.process_query(
                    workspace_id="ws_123",
                    query="Test query",
                    retrieval_strategy=RetrievalStrategy.HYBRID
                )
                
                assert result is not None
                mock_retrieve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rerank_results(self, rag_service):
        """Test result reranking"""
        results = [
            RetrievalResult(
                chunk_id="chunk_1",
                content="Content 1",
                score=0.8,
                metadata={"source": "doc1"}
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                content="Content 2",
                score=0.7,
                metadata={"source": "doc2"}
            )
        ]
        
        with patch.object(rag_service, 'cross_encoder_rerank') as mock_rerank:
            mock_rerank.return_value = [
                RerankedResult(
                    chunk_id="chunk_2",
                    content="Content 2",
                    original_score=0.7,
                    reranked_score=0.9
                ),
                RerankedResult(
                    chunk_id="chunk_1",
                    content="Content 1",
                    original_score=0.8,
                    reranked_score=0.85
                )
            ]
            
            reranked = await rag_service.rerank_results(
                results, 
                "Test query",
                RerankingMethod.CROSS_ENCODER
            )
            
            assert len(reranked) == 2
            assert reranked[0].reranked_score > reranked[1].reranked_score
            mock_rerank.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_query_no_results(self, rag_service):
        """Test query processing with no retrieval results"""
        with patch.object(rag_service, 'retrieve_similar_chunks') as mock_retrieve:
            mock_retrieve.return_value = []
            
            with patch.object(rag_service, 'generate_fallback_response') as mock_fallback:
                mock_fallback.return_value = {
                    "answer": "I don't have information about that topic.",
                    "sources": [],
                    "tokens_used": 50
                }
                
                result = await rag_service.process_query(
                    workspace_id="ws_123",
                    query="Test query"
                )
                
                assert result is not None
                assert "don't have information" in result["answer"]
                mock_fallback.assert_called_once()

class TestEnhancedEmbeddingsService:
    """Unit tests for EnhancedEmbeddingsService"""
    
    @pytest.fixture
    def embeddings_service(self):
        return EnhancedEmbeddingsService()
    
    def test_initialization(self, embeddings_service):
        """Test service initialization"""
        assert embeddings_service is not None
        assert hasattr(embeddings_service, 'model_name')
    
    @pytest.mark.asyncio
    async def test_generate_embedding_single(self, embeddings_service):
        """Test single embedding generation"""
        with patch.object(embeddings_service, 'model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
            
            embedding = await embeddings_service.generate_embedding("Test text")
            
            assert isinstance(embedding, list)
            assert len(embedding) == 5
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embeddings_service):
        """Test batch embedding generation"""
        with patch.object(embeddings_service, 'model') as mock_model:
            mock_model.encode.return_value = [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9]
            ]
            
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = await embeddings_service.generate_embeddings(texts)
            
            assert isinstance(embeddings, list)
            assert len(embeddings) == 3
            assert all(len(emb) == 3 for emb in embeddings)
    
    def test_get_model_info(self, embeddings_service):
        """Test model information retrieval"""
        info = embeddings_service.get_model_info()
        
        assert isinstance(info, dict)
        assert "model_name" in info
        assert "embedding_dimension" in info
        assert "model_type" in info
    
    def test_switch_model(self, embeddings_service):
        """Test model switching"""
        with patch.object(embeddings_service, '_load_model') as mock_load:
            mock_load.return_value = Mock()
            
            embeddings_service.switch_model(EmbeddingModel.ALL_MPNET_BASE_V2)
            
            mock_load.assert_called_once_with(EmbeddingModel.ALL_MPNET_BASE_V2)

class TestEnhancedVectorService:
    """Unit tests for EnhancedVectorService"""
    
    @pytest.fixture
    def vector_service(self):
        return EnhancedVectorService()
    
    def test_initialization(self, vector_service):
        """Test service initialization"""
        assert vector_service is not None
        assert hasattr(vector_service, 'search_mode')
        assert hasattr(vector_service, 'indexing_strategy')
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks(self, vector_service):
        """Test similar chunk search"""
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.query.return_value = {
                "documents": [["Test content"]],
                "metadatas": [[{"source": "doc1"}]],
                "distances": [[0.1]]
            }
            
            results = await vector_service.search_similar_chunks(
                query="Test query",
                workspace_id="ws_123",
                limit=5
            )
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert "content" in results[0]
            assert "score" in results[0]
    
    @pytest.mark.asyncio
    async def test_add_chunks(self, vector_service):
        """Test adding chunks to vector store"""
        chunks = [
            {
                "chunk_id": "chunk_1",
                "content": "Test content 1",
                "metadata": {"source": "doc1"}
            },
            {
                "chunk_id": "chunk_2", 
                "content": "Test content 2",
                "metadata": {"source": "doc2"}
            }
        ]
        
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.add.return_value = True
            
            result = await vector_service.add_chunks(
                chunks=chunks,
                workspace_id="ws_123"
            )
            
            assert result is True
            mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_chunks(self, vector_service):
        """Test deleting chunks from vector store"""
        chunk_ids = ["chunk_1", "chunk_2"]
        
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.delete.return_value = True
            
            result = await vector_service.delete_chunks(
                chunk_ids=chunk_ids,
                workspace_id="ws_123"
            )
            
            assert result is True
            mock_collection.delete.assert_called_once()

class TestEnhancedFileProcessor:
    """Unit tests for EnhancedFileProcessor"""
    
    @pytest.fixture
    def file_processor(self):
        return EnhancedFileProcessor()
    
    def test_initialization(self, file_processor):
        """Test processor initialization"""
        assert file_processor is not None
        assert hasattr(file_processor, 'chunking_strategy')
    
    @pytest.mark.asyncio
    async def test_process_file(self, file_processor):
        """Test file processing"""
        with patch.object(file_processor, 'extract_text') as mock_extract:
            mock_extract.return_value = "Test file content"
            
            with patch.object(file_processor, 'create_chunks') as mock_chunks:
                mock_chunks.return_value = [
                    TextBlock(
                        content="Chunk 1",
                        metadata={"chunk_index": 0}
                    )
                ]
                
                result = await file_processor.process_file(
                    file_path="test.txt",
                    content_type="text/plain"
                )
                
                assert isinstance(result, list)
                assert len(result) > 0
                mock_extract.assert_called_once()
                mock_chunks.assert_called_once()
    
    def test_create_chunks_semantic(self, file_processor):
        """Test semantic chunking"""
        text_blocks = [
            TextBlock(content="Block 1", metadata={}),
            TextBlock(content="Block 2", metadata={}),
            TextBlock(content="Block 3", metadata={})
        ]
        
        chunks = file_processor.create_chunks(
            text_blocks,
            strategy=ChunkingStrategy.SEMANTIC
        )
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
    
    def test_create_chunks_fixed(self, file_processor):
        """Test fixed-size chunking"""
        text_blocks = [
            TextBlock(content="Block 1", metadata={}),
            TextBlock(content="Block 2", metadata={}),
            TextBlock(content="Block 3", metadata={})
        ]
        
        chunks = file_processor.create_chunks(
            text_blocks,
            strategy=ChunkingStrategy.FIXED
        )
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0

class TestProductionRAGService:
    """Unit tests for ProductionRAGService"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    def test_initialization(self, rag_service):
        """Test service initialization"""
        assert rag_service is not None
        assert hasattr(rag_service, 'config')
    
    def test_config_creation(self, rag_service):
        """Test RAG configuration creation"""
        config = RAGConfig(
            mode=RAGMode.BALANCED,
            response_style=ResponseStyle.CONVERSATIONAL,
            max_tokens=1000,
            temperature=0.7
        )
        
        assert config.mode == RAGMode.BALANCED
        assert config.response_style == ResponseStyle.CONVERSATIONAL
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
    
    @pytest.mark.asyncio
    async def test_process_query_with_config(self, rag_service):
        """Test query processing with custom configuration"""
        config = RAGConfig(
            mode=RAGMode.ACCURACY,
            response_style=ResponseStyle.FORMAL,
            max_tokens=500
        )
        
        with patch.object(rag_service, 'retrieve_context') as mock_retrieve:
            mock_retrieve.return_value = [
                {"content": "Context 1", "score": 0.9},
                {"content": "Context 2", "score": 0.8}
            ]
            
            with patch.object(rag_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "answer": "Formal response",
                    "sources": [],
                    "tokens_used": 300
                }
                
                result = await rag_service.process_query(
                    workspace_id="ws_123",
                    query="Test query",
                    config=config
                )
                
                assert result is not None
                assert "answer" in result
                mock_retrieve.assert_called_once()
                mock_generate.assert_called_once()

class TestProductionVectorService:
    """Unit tests for ProductionVectorService"""
    
    @pytest.fixture
    def vector_service(self):
        return ProductionVectorService()
    
    def test_initialization(self, vector_service):
        """Test service initialization"""
        assert vector_service is not None
        assert hasattr(vector_service, 'search_mode')
    
    def test_search_config_creation(self, vector_service):
        """Test search configuration creation"""
        config = SearchConfig(
            mode=SearchMode.SIMILARITY,
            limit=10,
            threshold=0.7,
            rerank=True
        )
        
        assert config.mode == SearchMode.SIMILARITY
        assert config.limit == 10
        assert config.threshold == 0.7
        assert config.rerank is True
    
    @pytest.mark.asyncio
    async def test_search_with_config(self, vector_service):
        """Test search with custom configuration"""
        config = SearchConfig(
            mode=SearchMode.HYBRID,
            limit=5,
            threshold=0.8
        )
        
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.query.return_value = {
                "documents": [["Test content"]],
                "metadatas": [[{"source": "doc1"}]],
                "distances": [[0.1]]
            }
            
            results = await vector_service.search(
                query="Test query",
                workspace_id="ws_123",
                config=config
            )
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert all(isinstance(result, SearchResult) for result in results)
    
    @pytest.mark.asyncio
    async def test_index_documents(self, vector_service):
        """Test document indexing"""
        documents = [
            {
                "id": "doc_1",
                "content": "Document 1 content",
                "metadata": {"source": "file1.pdf"}
            },
            {
                "id": "doc_2",
                "content": "Document 2 content", 
                "metadata": {"source": "file2.pdf"}
            }
        ]
        
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.add.return_value = True
            
            result = await vector_service.index_documents(
                documents=documents,
                workspace_id="ws_123"
            )
            
            assert result is True
            mock_collection.add.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

