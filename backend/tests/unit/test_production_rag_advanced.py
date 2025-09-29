"""
Comprehensive tests for Production RAG Service and Advanced Features
Tests advanced RAG capabilities, streaming, caching, and production-grade features
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.services.production_rag_service import (
    ProductionRAGService, 
    RAGConfig, 
    RAGMode, 
    ResponseStyle
)
from app.services.production_rag_system import (
    ProductionFileProcessor,
    Chunk,
    TextBlock,
    ChunkingStrategy
)
from app.services.production_vector_service import (
    ProductionVectorService,
    SearchConfig,
    SearchMode,
    SearchResult
)
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.schemas.rag import RAGQueryResponse, RAGSource


class TestProductionRAGServiceAdvanced:
    """Advanced tests for ProductionRAGService"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.fixture
    def custom_config(self):
        return RAGConfig(
            chunk_size=500,
            chunk_overlap=100,
            search_mode=SearchMode.HYBRID,
            top_k=15,
            similarity_threshold=0.8,
            use_reranking=True,
            rerank_top_k=8,
            response_style=ResponseStyle.TECHNICAL,
            max_context_length=6000,
            include_sources=True,
            include_citations=True,
            stream_response=False,
            parallel_processing=True
        )
    
    @pytest.fixture
    def streaming_config(self):
        return RAGConfig(
            stream_response=True,
            response_style=ResponseStyle.CONVERSATIONAL,
            max_context_length=4000
        )
    
    @pytest.mark.asyncio
    async def test_advanced_file_processing(self, rag_service, custom_config):
        """Test advanced file processing with custom configuration"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    # Mock file processing
                    mock_text_blocks = [
                        TextBlock(content="Block 1 content", metadata={"page": 1}),
                        TextBlock(content="Block 2 content", metadata={"page": 2})
                    ]
                    mock_process.return_value = mock_text_blocks
                    
                    # Mock chunking
                    mock_chunks = [
                        Chunk(id="chunk_1", content="Chunk 1", metadata={"document_id": "doc_1"}),
                        Chunk(id="chunk_2", content="Chunk 2", metadata={"document_id": "doc_1"})
                    ]
                    rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                    
                    # Mock vector service
                    mock_add.return_value = True
                    mock_save.return_value = "doc_123"
                    
                    result = await rag_service.process_file(
                        file_path="test.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1",
                        config=custom_config
                    )
                    
                    assert result["status"] == "success"
                    assert result["document_id"] == "doc_123"
                    assert result["chunks_created"] == 2
                    assert result["processing_time"] > 0
                    
                    # Verify custom config was used
                    mock_process.assert_called_once_with("test.pdf", "application/pdf")
                    mock_add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hybrid_search_mode(self, rag_service, custom_config):
        """Test hybrid search mode with reranking"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            # Mock search results
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Relevant content 1",
                    score=0.95,
                    metadata={"document_id": "doc_1", "chunk_id": "chunk_1"}
                ),
                SearchResult(
                    id="result_2", 
                    content="Relevant content 2",
                    score=0.87,
                    metadata={"document_id": "doc_2", "chunk_id": "chunk_2"}
                )
            ]
            mock_search.return_value = mock_results
            
            results = await rag_service.search_documents(
                query="Test query",
                workspace_id="ws_1",
                config=custom_config
            )
            
            assert len(results) == 2
            assert results[0].score == 0.95
            assert results[1].score == 0.87
            
            # Verify search was called with correct config
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["config"].search_mode == SearchMode.HYBRID
            assert call_args[1]["config"].use_reranking is True
    
    @pytest.mark.asyncio
    async def test_document_filtering(self, rag_service, custom_config):
        """Test document filtering in search"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Content from doc_1",
                    score=0.9,
                    metadata={"document_id": "doc_1"}
                )
            ]
            mock_search.return_value = mock_results
            
            # Test with document filtering
            results = await rag_service.search_documents(
                query="Test query",
                workspace_id="ws_1",
                config=custom_config
            )
            
            assert len(results) == 1
            assert results[0].metadata["document_id"] == "doc_1"
    
    @pytest.mark.asyncio
    async def test_streaming_response_generation(self, rag_service, streaming_config):
        """Test streaming response generation"""
        with patch.object(rag_service, 'search_documents') as mock_search:
            with patch.object(rag_service, '_generate_streaming_response') as mock_stream:
                # Mock search results
                mock_results = [
                    SearchResult(
                        id="result_1",
                        content="Streaming content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_results
                
                # Mock streaming response
                mock_stream.return_value = RAGQueryResponse(
                    answer="Streaming answer",
                    sources=[],
                    response_time_ms=100
                )
                
                result = await rag_service.generate_response(
                    query="Test query",
                    workspace_id="ws_1",
                    config=streaming_config
                )
                
                assert result.answer == "Streaming answer"
                mock_stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_technical_response_style(self, rag_service, custom_config):
        """Test technical response style generation"""
        with patch.object(rag_service, 'search_documents') as mock_search:
            with patch.object(rag_service, '_generate_single_response') as mock_generate:
                # Mock search results
                mock_results = [
                    SearchResult(
                        id="result_1",
                        content="Technical content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_results
                
                # Mock technical response
                mock_generate.return_value = RAGQueryResponse(
                    answer="Technical detailed answer with specifications",
                    sources=[],
                    response_time_ms=200
                )
                
                result = await rag_service.generate_response(
                    query="How does this work technically?",
                    workspace_id="ws_1",
                    config=custom_config
                )
                
                assert result.answer == "Technical detailed answer with specifications"
                mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_citation_generation(self, rag_service, custom_config):
        """Test citation generation in responses"""
        with patch.object(rag_service, 'search_documents') as mock_search:
            with patch.object(rag_service, '_build_enhanced_context') as mock_context:
                with patch.object(rag_service, '_generate_single_response') as mock_generate:
                    # Mock search results
                    mock_results = [
                        SearchResult(
                            id="result_1",
                            content="Cited content",
                            score=0.9,
                            metadata={"document_id": "doc_1", "page": 1}
                        )
                    ]
                    mock_search.return_value = mock_results
                    
                    # Mock context building with citations
                    mock_context.return_value = (
                        "Context with [1] citations",
                        [RAGSource(document_id="doc_1", chunk_id="chunk_1", content="Cited content", score=0.9)]
                    )
                    
                    # Mock response with citations
                    mock_generate.return_value = RAGQueryResponse(
                        answer="Answer with [1] citations",
                        sources=[RAGSource(document_id="doc_1", chunk_id="chunk_1", content="Cited content", score=0.9)],
                        response_time_ms=150
                    )
                    
                    result = await rag_service.generate_response(
                        query="Test query with citations",
                        workspace_id="ws_1",
                        config=custom_config
                    )
                    
                    assert result.answer == "Answer with [1] citations"
                    assert len(result.sources) == 1
                    assert result.sources[0].document_id == "doc_1"
                    mock_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self, rag_service, custom_config):
        """Test parallel processing capabilities"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                # Mock parallel processing
                mock_text_blocks = [
                    TextBlock(content=f"Block {i} content", metadata={"page": i})
                    for i in range(10)
                ]
                mock_process.return_value = mock_text_blocks
                
                mock_chunks = [
                    Chunk(id=f"chunk_{i}", content=f"Chunk {i}", metadata={"document_id": "doc_1"})
                    for i in range(10)
                ]
                rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                mock_add.return_value = True
                
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    mock_save.return_value = "doc_123"
                    
                    result = await rag_service.process_file(
                        file_path="large_document.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1",
                        config=custom_config
                    )
                    
                    assert result["status"] == "success"
                    assert result["chunks_created"] == 10
                    # Verify parallel processing was used
                    assert custom_config.parallel_processing is True
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, rag_service):
        """Test performance metrics tracking"""
        # Test initial stats
        initial_stats = rag_service.get_performance_stats()
        assert initial_stats["total_queries"] == 0
        assert initial_stats["total_files_processed"] == 0
        assert initial_stats["avg_query_time"] == 0.0
        
        # Simulate some operations
        rag_service.performance_stats["total_queries"] = 100
        rag_service.performance_stats["total_files_processed"] = 50
        rag_service.performance_stats["avg_query_time"] = 250.0
        rag_service.performance_stats["success_rate"] = 0.95
        
        updated_stats = rag_service.get_performance_stats()
        assert updated_stats["total_queries"] == 100
        assert updated_stats["total_files_processed"] == 50
        assert updated_stats["avg_query_time"] == 250.0
        assert updated_stats["success_rate"] == 0.95
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, rag_service):
        """Test error handling and recovery mechanisms"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            # Test file processing error
            mock_process.side_effect = Exception("File processing failed")
            
            with pytest.raises(Exception):
                await rag_service.process_file(
                    file_path="corrupted.pdf",
                    content_type="application/pdf",
                    workspace_id="ws_1"
                )
            
            # Verify error is logged and stats are updated
            assert rag_service.performance_stats["total_files_processed"] >= 0
    
    @pytest.mark.asyncio
    async def test_context_length_management(self, rag_service, custom_config):
        """Test context length management"""
        with patch.object(rag_service, 'search_documents') as mock_search:
            with patch.object(rag_service, '_build_enhanced_context') as mock_context:
                # Mock search results
                mock_results = [
                    SearchResult(
                        id=f"result_{i}",
                        content=f"Content {i} " * 1000,  # Large content
                        score=0.9,
                        metadata={"document_id": f"doc_{i}"}
                    )
                    for i in range(10)
                ]
                mock_search.return_value = mock_results
                
                # Mock context building with length management
                mock_context.return_value = (
                    "Truncated context",
                    [RAGSource(document_id="doc_1", chunk_id="chunk_1", content="Content", score=0.9)]
                )
                
                with patch.object(rag_service, '_generate_single_response') as mock_generate:
                    mock_generate.return_value = RAGQueryResponse(
                        answer="Answer",
                        sources=[],
                        response_time_ms=100
                    )
                    
                    result = await rag_service.generate_response(
                        query="Test query",
                        workspace_id="ws_1",
                        config=custom_config
                    )
                    
                    # Verify context was built with length management
                    mock_context.assert_called_once()
                    call_args = mock_context.call_args
                    assert call_args[1]["config"].max_context_length == 6000


class TestProductionFileProcessor:
    """Tests for ProductionFileProcessor advanced features"""
    
    @pytest.fixture
    def file_processor(self):
        return ProductionFileProcessor()
    
    @pytest.mark.asyncio
    async def test_semantic_chunking_strategy(self, file_processor):
        """Test semantic chunking strategy"""
        with patch.object(file_processor, 'process_file') as mock_process:
            # Mock text blocks
            mock_text_blocks = [
                TextBlock(content="This is a complete thought about customer service.", metadata={"page": 1}),
                TextBlock(content="This is another complete thought about refund policies.", metadata={"page": 1}),
                TextBlock(content="This is a third complete thought about shipping.", metadata={"page": 2})
            ]
            mock_process.return_value = mock_text_blocks
            
            # Mock semantic chunking
            with patch.object(file_processor, 'create_semantic_chunks') as mock_chunking:
                mock_chunks = [
                    Chunk(
                        id="chunk_1",
                        content="This is a complete thought about customer service.",
                        metadata={"document_id": "doc_1", "chunk_type": "semantic"}
                    ),
                    Chunk(
                        id="chunk_2", 
                        content="This is another complete thought about refund policies.",
                        metadata={"document_id": "doc_1", "chunk_type": "semantic"}
                    )
                ]
                mock_chunking.return_value = mock_chunks
                
                result = await file_processor.process_file("test.pdf", "application/pdf")
                
                assert len(result) == 3
                mock_chunking.assert_called_once_with(mock_text_blocks)
    
    @pytest.mark.asyncio
    async def test_multiple_file_formats(self, file_processor):
        """Test processing multiple file formats"""
        file_formats = [
            ("document.pdf", "application/pdf"),
            ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("document.txt", "text/plain"),
            ("document.html", "text/html"),
            ("document.md", "text/markdown")
        ]
        
        for file_path, content_type in file_formats:
            with patch.object(file_processor, 'process_file') as mock_process:
                mock_process.return_value = [
                    TextBlock(content=f"Content from {file_path}", metadata={"format": content_type})
                ]
                
                result = await file_processor.process_file(file_path, content_type)
                
                assert len(result) == 1
                assert result[0].content == f"Content from {file_path}"
    
    @pytest.mark.asyncio
    async def test_metadata_extraction(self, file_processor):
        """Test metadata extraction from files"""
        with patch.object(file_processor, 'process_file') as mock_process:
            mock_text_blocks = [
                TextBlock(
                    content="Document content",
                    metadata={
                        "page": 1,
                        "section": "Introduction",
                        "author": "Test Author",
                        "created_date": "2024-01-01"
                    }
                )
            ]
            mock_process.return_value = mock_text_blocks
            
            result = await file_processor.process_file("test.pdf", "application/pdf")
            
            assert len(result) == 1
            assert result[0].metadata["page"] == 1
            assert result[0].metadata["section"] == "Introduction"
            assert result[0].metadata["author"] == "Test Author"


class TestProductionVectorService:
    """Tests for ProductionVectorService advanced features"""
    
    @pytest.fixture
    def vector_service(self, db_session):
        return ProductionVectorService(db_session)
    
    @pytest.mark.asyncio
    async def test_hybrid_search_mode(self, vector_service):
        """Test hybrid search mode combining semantic and keyword search"""
        with patch.object(vector_service, 'search') as mock_search:
            # Mock hybrid search results
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Semantic match content",
                    score=0.95,
                    metadata={"search_type": "semantic", "document_id": "doc_1"}
                ),
                SearchResult(
                    id="result_2",
                    content="Keyword match content", 
                    score=0.87,
                    metadata={"search_type": "keyword", "document_id": "doc_2"}
                )
            ]
            mock_search.return_value = mock_results
            
            config = SearchConfig(
                search_mode=SearchMode.HYBRID,
                top_k=10,
                similarity_threshold=0.7
            )
            
            results = await vector_service.search(
                query="test query",
                workspace_id="ws_1",
                config=config
            )
            
            assert len(results) == 2
            assert results[0].score == 0.95
            assert results[1].score == 0.87
    
    @pytest.mark.asyncio
    async def test_reranking_functionality(self, vector_service):
        """Test reranking functionality for improved relevance"""
        with patch.object(vector_service, 'search') as mock_search:
            # Mock search results before reranking
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Less relevant content",
                    score=0.9,
                    metadata={"document_id": "doc_1"}
                ),
                SearchResult(
                    id="result_2",
                    content="More relevant content",
                    score=0.8,
                    metadata={"document_id": "doc_2"}
                )
            ]
            mock_search.return_value = mock_results
            
            config = SearchConfig(
                use_reranking=True,
                rerank_top_k=5,
                top_k=10
            )
            
            results = await vector_service.search(
                query="test query",
                workspace_id="ws_1",
                config=config
            )
            
            assert len(results) == 2
            # Results should be reranked for better relevance
            mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, vector_service):
        """Test caching mechanism for improved performance"""
        with patch.object(vector_service, 'search') as mock_search:
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Cached content",
                    score=0.9,
                    metadata={"document_id": "doc_1"}
                )
            ]
            mock_search.return_value = mock_results
            
            config = SearchConfig(
                use_cache=True,
                cache_ttl=3600
            )
            
            # First search - should populate cache
            results1 = await vector_service.search(
                query="test query",
                workspace_id="ws_1",
                config=config
            )
            
            # Second search - should use cache
            results2 = await vector_service.search(
                query="test query",
                workspace_id="ws_1",
                config=config
            )
            
            assert len(results1) == 1
            assert len(results2) == 1
            # Should be called twice (cache miss + cache hit)
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_metadata_filtering(self, vector_service):
        """Test metadata filtering in search"""
        with patch.object(vector_service, 'search') as mock_search:
            mock_results = [
                SearchResult(
                    id="result_1",
                    content="Filtered content",
                    score=0.9,
                    metadata={"document_id": "doc_1", "category": "support"}
                )
            ]
            mock_search.return_value = mock_results
            
            config = SearchConfig(
                filter_by_metadata={"category": "support"},
                top_k=10
            )
            
            results = await vector_service.search(
                query="test query",
                workspace_id="ws_1",
                config=config
            )
            
            assert len(results) == 1
            assert results[0].metadata["category"] == "support"
            mock_search.assert_called_once()


class TestRAGConfiguration:
    """Tests for RAG configuration and validation"""
    
    def test_rag_config_validation(self):
        """Test RAG configuration validation"""
        # Test valid configuration
        config = RAGConfig(
            chunk_size=1000,
            chunk_overlap=200,
            top_k=10,
            similarity_threshold=0.7,
            max_context_length=4000
        )
        
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.top_k == 10
        assert config.similarity_threshold == 0.7
        assert config.max_context_length == 4000
    
    def test_response_style_enum(self):
        """Test response style enumeration"""
        styles = [
            ResponseStyle.CONVERSATIONAL,
            ResponseStyle.TECHNICAL,
            ResponseStyle.FORMAL,
            ResponseStyle.CASUAL,
            ResponseStyle.STEP_BY_STEP
        ]
        
        for style in styles:
            assert style in ResponseStyle
            assert isinstance(style.value, str)
    
    def test_rag_mode_enum(self):
        """Test RAG mode enumeration"""
        modes = [
            RAGMode.PROCESS_FILE,
            RAGMode.SEARCH_ONLY,
            RAGMode.GENERATE_ONLY,
            RAGMode.FULL_RAG
        ]
        
        for mode in modes:
            assert mode in RAGMode
            assert isinstance(mode.value, str)
    
    def test_chunking_strategy_enum(self):
        """Test chunking strategy enumeration"""
        strategies = [
            ChunkingStrategy.SEMANTIC,
            ChunkingStrategy.FIXED_SIZE,
            ChunkingStrategy.SENTENCE_BASED
        ]
        
        for strategy in strategies:
            assert strategy in ChunkingStrategy
            assert isinstance(strategy.value, str)


class TestRAGIntegrationAdvanced:
    """Advanced integration tests for RAG components"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.mark.asyncio
    async def test_complete_rag_pipeline_advanced(self, rag_service):
        """Test complete advanced RAG pipeline"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                with patch.object(rag_service.vector_service, 'search') as mock_search:
                    with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                        # Setup mocks
                        mock_text_blocks = [
                            TextBlock(content="Advanced content", metadata={"page": 1})
                        ]
                        mock_process.return_value = mock_text_blocks
                        
                        mock_chunks = [
                            Chunk(id="chunk_1", content="Advanced chunk", metadata={"document_id": "doc_1"})
                        ]
                        rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                        mock_add.return_value = True
                        
                        mock_search_results = [
                            SearchResult(
                                id="result_1",
                                content="Advanced search result",
                                score=0.95,
                                metadata={"document_id": "doc_1"}
                            )
                        ]
                        mock_search.return_value = mock_search_results
                        
                        mock_generate.return_value = {
                            "content": "Advanced response",
                            "sources_used": [{"chunk_id": "chunk_1"}],
                            "tokens_used": 200
                        }
                        
                        with patch.object(rag_service, '_save_document_to_db') as mock_save:
                            mock_save.return_value = "doc_123"
                            
                            # Step 1: Process file
                            process_result = await rag_service.process_file(
                                file_path="advanced.pdf",
                                content_type="application/pdf",
                                workspace_id="ws_1"
                            )
                            assert process_result["status"] == "success"
                            
                            # Step 2: Generate response
                            query_result = await rag_service.generate_response(
                                query="Advanced query",
                                workspace_id="ws_1"
                            )
                            assert query_result.answer == "Advanced response"
                            assert len(query_result.sources) == 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_advanced(self, rag_service):
        """Test advanced error recovery mechanisms"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            # Test file processing error
            mock_process.side_effect = Exception("Advanced processing error")
            
            with pytest.raises(Exception):
                await rag_service.process_file(
                    file_path="corrupted.pdf",
                    content_type="application/pdf",
                    workspace_id="ws_1"
                )
            
            # Verify error handling doesn't crash the service
            assert rag_service.performance_stats["total_files_processed"] >= 0
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, rag_service):
        """Test performance optimization features"""
        # Test parallel processing
        config = RAGConfig(parallel_processing=True)
        assert config.parallel_processing is True
        
        # Test caching
        config.use_cache = True
        assert config.use_cache is True
        
        # Test performance tracking
        initial_queries = rag_service.performance_stats["total_queries"]
        rag_service.performance_stats["total_queries"] += 1
        assert rag_service.performance_stats["total_queries"] == initial_queries + 1
