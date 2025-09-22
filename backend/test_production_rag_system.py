"""
Comprehensive test for production-grade RAG system
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.production_rag_system import (
    ProductionFileProcessor,
    ChunkingStrategy,
    FileType
)
from app.services.production_vector_service import (
    ProductionVectorService,
    SearchMode,
    SearchConfig
)
from app.services.production_rag_service import (
    ProductionRAGService,
    RAGConfig,
    ResponseStyle
)


class TestProductionFileProcessor:
    """Test production file processor"""
    
    @pytest.fixture
    def processor(self):
        return ProductionFileProcessor(
            chunk_size=500,
            chunk_overlap=100,
            chunking_strategy=ChunkingStrategy.SEMANTIC
        )
    
    @pytest.mark.asyncio
    async def test_process_text_file(self, processor):
        """Test processing text file"""
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            This is a test document.
            
            It contains multiple paragraphs.
            
            Each paragraph should be processed separately.
            """)
            temp_file = f.name
        
        try:
            # Process file
            text_blocks = await processor.process_file(temp_file, FileType.TXT.value)
            
            # Verify results
            assert len(text_blocks) > 0
            assert all(hasattr(block, 'text') for block in text_blocks)
            assert all(hasattr(block, 'metadata') for block in text_blocks)
            assert all(hasattr(block, 'importance_score') for block in text_blocks)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_process_markdown_file(self, processor):
        """Test processing markdown file"""
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
            # Main Title
            
            This is a paragraph under the main title.
            
            ## Subtitle
            
            This is a paragraph under the subtitle.
            
            ### Sub-subtitle
            
            This is a paragraph under the sub-subtitle.
            """)
            temp_file = f.name
        
        try:
            # Process file
            text_blocks = await processor.process_file(temp_file, FileType.MD.value)
            
            # Verify results
            assert len(text_blocks) > 0
            
            # Check for title blocks
            title_blocks = [b for b in text_blocks if b.block_type == 'title']
            assert len(title_blocks) > 0
            
            # Check for subtitle blocks
            subtitle_blocks = [b for b in text_blocks if b.block_type == 'subtitle']
            assert len(subtitle_blocks) > 0
            
        finally:
            os.unlink(temp_file)
    
    def test_create_semantic_chunks(self, processor):
        """Test creating semantic chunks"""
        # Create test text blocks
        text_blocks = [
            processor.TextBlock(
                text="This is the first paragraph.",
                block_type="paragraph",
                importance_score=0.7
            ),
            processor.TextBlock(
                text="This is the second paragraph.",
                block_type="paragraph",
                importance_score=0.8
            ),
            processor.TextBlock(
                text="This is a title.",
                block_type="title",
                importance_score=0.9
            )
        ]
        
        # Create chunks
        chunks = processor.create_semantic_chunks(text_blocks)
        
        # Verify results
        assert len(chunks) > 0
        assert all(hasattr(chunk, 'text') for chunk in chunks)
        assert all(hasattr(chunk, 'chunk_id') for chunk in chunks)
        assert all(hasattr(chunk, 'metadata') for chunk in chunks)
        assert all(hasattr(chunk, 'importance_score') for chunk in chunks)
    
    def test_text_classification(self, processor):
        """Test text block classification"""
        # Test title classification
        title_text = "This is a Title"
        block_type = processor._classify_text_block_advanced(title_text)
        assert block_type == "title"
        
        # Test list classification
        list_text = "1. First item\n2. Second item"
        block_type = processor._classify_text_block_advanced(list_text)
        assert block_type == "list"
        
        # Test question classification
        question_text = "What is the purpose of this system?"
        block_type = processor._classify_text_block_advanced(question_text)
        assert block_type == "question"
    
    def test_importance_scoring(self, processor):
        """Test importance score calculation"""
        # Test title importance
        title_text = "Important Title"
        score = processor._calculate_importance_score_advanced(title_text, "title")
        assert score > 0.8
        
        # Test paragraph importance
        para_text = "This is a regular paragraph."
        score = processor._calculate_importance_score_advanced(para_text, "paragraph")
        assert 0.4 <= score <= 0.6


class TestProductionVectorService:
    """Test production vector service"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def vector_service(self, mock_db):
        with patch('app.services.production_vector_service.CHROMADB_AVAILABLE', True):
            with patch('app.services.production_vector_service.ML_AVAILABLE', True):
                with patch('app.services.production_vector_service.REDIS_AVAILABLE', True):
                    return ProductionVectorService(mock_db)
    
    @pytest.mark.asyncio
    async def test_add_chunks(self, vector_service):
        """Test adding chunks to vector database"""
        # Create test chunks
        chunks = [
            vector_service.Chunk(
                text="Test chunk 1",
                chunk_id="chunk1",
                document_id=1,
                workspace_id="workspace1",
                chunk_index=0,
                metadata={"test": "data"}
            ),
            vector_service.Chunk(
                text="Test chunk 2",
                chunk_id="chunk2",
                document_id=1,
                workspace_id="workspace1",
                chunk_index=1,
                metadata={"test": "data"}
            )
        ]
        
        # Mock ChromaDB collection
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.add.return_value = None
            
            # Add chunks
            result = await vector_service.add_chunks(chunks, "workspace1")
            
            # Verify result
            assert result is True
            mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search(self, vector_service):
        """Test vector search"""
        # Mock ChromaDB collection
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.query.return_value = {
                'ids': [['chunk1', 'chunk2']],
                'documents': [['Test chunk 1', 'Test chunk 2']],
                'metadatas': [[{'document_id': 1}, {'document_id': 1}]],
                'distances': [[0.1, 0.2]]
            }
            
            # Mock embedding generation
            with patch.object(vector_service, '_generate_embedding') as mock_embedding:
                mock_embedding.return_value = [0.1] * 384
                
                # Perform search
                results = await vector_service.search(
                    query="test query",
                    workspace_id="workspace1"
                )
                
                # Verify results
                assert len(results) == 2
                assert results[0].chunk_id == "chunk1"
                assert results[1].chunk_id == "chunk2"
    
    @pytest.mark.asyncio
    async def test_health_check(self, vector_service):
        """Test health check"""
        # Mock components
        with patch.object(vector_service, 'collection') as mock_collection:
            mock_collection.count.return_value = 100
            
            with patch.object(vector_service, 'redis_client') as mock_redis:
                mock_redis.ping.return_value = True
                
                with patch.object(vector_service, 'embedding_model') as mock_model:
                    mock_model.encode.return_value = [0.1] * 384
                    
                    # Perform health check
                    health = await vector_service.health_check()
                    
                    # Verify health status
                    assert health["status"] in ["healthy", "degraded"]
                    assert "components" in health
                    assert "timestamp" in health


class TestProductionRAGService:
    """Test production RAG service"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        with patch('app.services.production_rag_service.ProductionFileProcessor'):
            with patch('app.services.production_rag_service.ProductionVectorService'):
                with patch('app.services.production_rag_service.GeminiService'):
                    return ProductionRAGService(mock_db)
    
    @pytest.mark.asyncio
    async def test_process_file(self, rag_service):
        """Test file processing"""
        # Mock file processor
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            mock_process.return_value = [
                rag_service.file_processor.TextBlock(
                    text="Test content",
                    block_type="paragraph",
                    importance_score=0.7
                )
            ]
            
            # Mock vector service
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                mock_add.return_value = True
                
                # Mock database save
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    mock_save.return_value = 1
                    
                    # Process file
                    result = await rag_service.process_file(
                        file_path="test.txt",
                        content_type="text/plain",
                        workspace_id="workspace1"
                    )
                    
                    # Verify result
                    assert result["success"] is True
                    assert "document_id" in result
                    assert "chunks_created" in result
    
    @pytest.mark.asyncio
    async def test_search_documents(self, rag_service):
        """Test document search"""
        # Mock vector service search
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            mock_search.return_value = [
                rag_service.vector_service.SearchResult(
                    chunk_id="chunk1",
                    document_id=1,
                    text="Test content",
                    score=0.9,
                    metadata={"test": "data"}
                )
            ]
            
            # Perform search
            results = await rag_service.search_documents(
                query="test query",
                workspace_id="workspace1"
            )
            
            # Verify results
            assert len(results) == 1
            assert results[0].chunk_id == "chunk1"
            assert results[0].score == 0.9
    
    @pytest.mark.asyncio
    async def test_generate_response(self, rag_service):
        """Test response generation"""
        # Mock search results
        search_results = [
            rag_service.vector_service.SearchResult(
                chunk_id="chunk1",
                document_id=1,
                text="Test content",
                score=0.9,
                metadata={"test": "data"}
            )
        ]
        
        # Mock Gemini service
        with patch.object(rag_service.gemini_service, 'generate_response') as mock_gemini:
            mock_gemini.return_value = {
                "response": "This is a test response.",
                "confidence": 0.8
            }
            
            # Generate response
            response = await rag_service.generate_response(
                query="test query",
                workspace_id="workspace1",
                context="Test context",
                sources=[{"id": "[1]", "chunk_id": "chunk1"}]
            )
            
            # Verify response
            assert response.answer == "This is a test response."
            assert response.confidence == 0.8
            assert len(response.sources) > 0
    
    @pytest.mark.asyncio
    async def test_process_query(self, rag_service):
        """Test full query processing"""
        # Mock all dependencies
        with patch.object(rag_service, 'search_documents') as mock_search:
            mock_search.return_value = [
                rag_service.vector_service.SearchResult(
                    chunk_id="chunk1",
                    document_id=1,
                    text="Test content",
                    score=0.9,
                    metadata={"test": "data"}
                )
            ]
            
            with patch.object(rag_service, 'generate_response') as mock_generate:
                mock_generate.return_value = rag_service.RAGQueryResponse(
                    answer="Test answer",
                    sources=[],
                    confidence=0.8,
                    query="test query",
                    context_used="test context",
                    processing_time=0.1,
                    metadata={}
                )
                
                with patch.object(rag_service, '_get_or_create_session') as mock_session:
                    mock_session.return_value = Mock()
                    
                    with patch.object(rag_service, '_save_interaction') as mock_save:
                        mock_save.return_value = None
                        
                        # Process query
                        response = await rag_service.process_query(
                            query="test query",
                            workspace_id="workspace1"
                        )
                        
                        # Verify response
                        assert response.answer == "Test answer"
                        assert response.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_health_check(self, rag_service):
        """Test health check"""
        # Mock component health checks
        with patch.object(rag_service.vector_service, 'health_check') as mock_vector_health:
            mock_vector_health.return_value = {"status": "healthy"}
            
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_gemini:
                mock_gemini.return_value = {"response": "test"}
                
                with patch.object(rag_service.file_processor, 'process_file') as mock_file:
                    mock_file.return_value = []
                    
                    # Perform health check
                    health = await rag_service.health_check()
                    
                    # Verify health status
                    assert health["status"] in ["healthy", "degraded"]
                    assert "components" in health
                    assert "timestamp" in health


class TestRAGConfigurations:
    """Test different RAG configurations"""
    
    def test_chunking_strategies(self):
        """Test different chunking strategies"""
        processor = ProductionFileProcessor(
            chunking_strategy=ChunkingStrategy.SEMANTIC
        )
        assert processor.chunking_strategy == ChunkingStrategy.SEMANTIC
        
        processor = ProductionFileProcessor(
            chunking_strategy=ChunkingStrategy.HIERARCHICAL
        )
        assert processor.chunking_strategy == ChunkingStrategy.HIERARCHICAL
    
    def test_search_modes(self):
        """Test different search modes"""
        config = SearchConfig(search_mode=SearchMode.HYBRID)
        assert config.search_mode == SearchMode.HYBRID
        
        config = SearchConfig(search_mode=SearchMode.SEMANTIC)
        assert config.search_mode == SearchMode.SEMANTIC
    
    def test_response_styles(self):
        """Test different response styles"""
        config = RAGConfig(response_style=ResponseStyle.TECHNICAL)
        assert config.response_style == ResponseStyle.TECHNICAL
        
        config = RAGConfig(response_style=ResponseStyle.CONVERSATIONAL)
        assert config.response_style == ResponseStyle.CONVERSATIONAL


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete integration workflow"""
    # This would test the complete workflow from file upload to response generation
    # For now, just verify the components can be instantiated
    
    # Mock database
    mock_db = Mock(spec=Session)
    
    # Test file processor
    processor = ProductionFileProcessor()
    assert processor is not None
    
    # Test vector service (with mocked dependencies)
    with patch('app.services.production_vector_service.CHROMADB_AVAILABLE', True):
        with patch('app.services.production_vector_service.ML_AVAILABLE', True):
            vector_service = ProductionVectorService(mock_db)
            assert vector_service is not None
    
    # Test RAG service (with mocked dependencies)
    with patch('app.services.production_rag_service.ProductionFileProcessor'):
        with patch('app.services.production_rag_service.ProductionVectorService'):
            with patch('app.services.production_rag_service.GeminiService'):
                rag_service = ProductionRAGService(mock_db)
                assert rag_service is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
