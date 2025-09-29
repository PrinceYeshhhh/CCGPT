"""
Performance tests for Production RAG Service
Tests advanced performance features, caching, and optimization
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.production_rag_service import (
    ProductionRAGService, 
    RAGConfig, 
    RAGMode, 
    ResponseStyle
)
from app.services.production_rag_system import ChunkingStrategy
from app.services.production_vector_service import SearchMode


class TestProductionRAGPerformance:
    """Performance tests for Production RAG Service"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.fixture
    def performance_config(self):
        return RAGConfig(
            chunk_size=1000,
            chunk_overlap=200,
            search_mode=SearchMode.HYBRID,
            top_k=10,
            similarity_threshold=0.7,
            use_reranking=True,
            rerank_top_k=5,
            response_style=ResponseStyle.CONVERSATIONAL,
            max_context_length=4000,
            include_sources=True,
            include_citations=True,
            stream_response=False,
            parallel_processing=True,
            use_cache=True,
            cache_ttl=3600
        )
    
    @pytest.mark.asyncio
    async def test_query_response_time_performance(self, rag_service, performance_config):
        """Test query response time performance"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Performance test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Performance test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Test multiple queries and measure response times
                response_times = []
                for i in range(20):
                    start_time = time.time()
                    response = await rag_service.generate_response(
                        query=f"Performance test query {i}",
                        workspace_id="ws_1",
                        config=performance_config
                    )
                    end_time = time.time()
                    
                    response_times.append(end_time - start_time)
                    assert response.answer == "Performance test response"
                
                # Analyze response times
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                # Performance assertions
                assert avg_response_time < 1.0  # Average under 1 second
                assert max_response_time < 2.0  # Max under 2 seconds
                assert min_response_time > 0.0  # Min greater than 0
                
                print(f"Average response time: {avg_response_time:.3f}s")
                print(f"Max response time: {max_response_time:.3f}s")
                print(f"Min response time: {min_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, rag_service, performance_config):
        """Test concurrent query performance"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Concurrent test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Concurrent test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Test concurrent queries
                start_time = time.time()
                tasks = []
                for i in range(50):  # 50 concurrent queries
                    task = rag_service.generate_response(
                        query=f"Concurrent test query {i}",
                        workspace_id="ws_1",
                        config=performance_config
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 50
                assert all(result.answer == "Concurrent test response" for result in results)
                
                # Should complete in reasonable time
                total_time = end_time - start_time
                assert total_time < 10.0  # Should complete within 10 seconds
                
                print(f"50 concurrent queries completed in {total_time:.3f}s")
                print(f"Average time per query: {total_time/50:.3f}s")
    
    @pytest.mark.asyncio
    async def test_caching_performance(self, rag_service, performance_config):
        """Test caching performance benefits"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Caching test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Caching test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # First query - cache miss
                start_time = time.time()
                response1 = await rag_service.generate_response(
                    query="Caching test query",
                    workspace_id="ws_1",
                    config=performance_config
                )
                first_query_time = time.time() - start_time
                
                # Second query - cache hit
                start_time = time.time()
                response2 = await rag_service.generate_response(
                    query="Caching test query",
                    workspace_id="ws_1",
                    config=performance_config
                )
                second_query_time = time.time() - start_time
                
                # Both responses should be identical
                assert response1.answer == response2.answer
                assert response1.answer == "Caching test response"
                
                # Cache hit should be faster (or at least not slower)
                assert second_query_time <= first_query_time
                
                print(f"First query time (cache miss): {first_query_time:.3f}s")
                print(f"Second query time (cache hit): {second_query_time:.3f}s")
                print(f"Cache performance improvement: {((first_query_time - second_query_time) / first_query_time * 100):.1f}%")
    
    @pytest.mark.asyncio
    async def test_large_document_processing_performance(self, rag_service, performance_config):
        """Test large document processing performance"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    # Mock large document processing
                    from app.services.production_rag_system import TextBlock
                    large_text_blocks = [
                        TextBlock(content=f"Large content block {i} " * 100, metadata={"page": i})
                        for i in range(1000)  # 1000 pages of content
                    ]
                    mock_process.return_value = large_text_blocks
                    
                    from app.services.production_rag_system import Chunk
                    large_chunks = [
                        Chunk(id=f"chunk_{i}", content=f"Large chunk {i}", metadata={"document_id": "doc_1"})
                        for i in range(1000)
                    ]
                    rag_service.file_processor.create_semantic_chunks = Mock(return_value=large_chunks)
                    mock_add.return_value = True
                    mock_save.return_value = "doc_large"
                    
                    start_time = time.time()
                    result = await rag_service.process_file(
                        file_path="large_document.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1",
                        config=performance_config
                    )
                    processing_time = time.time() - start_time
                    
                    assert result["status"] == "success"
                    assert result["chunks_created"] == 1000
                    assert processing_time < 30.0  # Should complete within 30 seconds
                    
                    print(f"Large document processing time: {processing_time:.3f}s")
                    print(f"Chunks per second: {1000/processing_time:.1f}")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, rag_service, performance_config):
        """Test memory usage under load"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Memory test content " * 1000,  # Large content
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Memory test response " * 100,  # Large response
                    "sources_used": [],
                    "tokens_used": 1000
                }
                
                # Test memory usage with many concurrent queries
                start_time = time.time()
                tasks = []
                for i in range(100):  # 100 concurrent queries with large content
                    task = rag_service.generate_response(
                        query=f"Memory test query {i}",
                        workspace_id="ws_1",
                        config=performance_config
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 100
                assert all("Memory test response" in result.answer for result in results)
                
                # Should complete without memory issues
                total_time = end_time - start_time
                assert total_time < 20.0  # Should complete within 20 seconds
                
                print(f"100 memory-intensive queries completed in {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_reranking_performance(self, rag_service, performance_config):
        """Test reranking performance impact"""
        # Test without reranking
        config_no_rerank = RAGConfig(
            use_reranking=False,
            top_k=10,
            similarity_threshold=0.7
        )
        
        # Test with reranking
        config_with_rerank = RAGConfig(
            use_reranking=True,
            rerank_top_k=5,
            top_k=10,
            similarity_threshold=0.7
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id=f"result_{i}",
                        content=f"Reranking test content {i}",
                        score=0.9 - (i * 0.01),  # Decreasing scores
                        metadata={"document_id": f"doc_{i}"}
                    )
                    for i in range(10)
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Reranking test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Test without reranking
                start_time = time.time()
                response1 = await rag_service.generate_response(
                    query="Reranking test query",
                    workspace_id="ws_1",
                    config=config_no_rerank
                )
                no_rerank_time = time.time() - start_time
                
                # Test with reranking
                start_time = time.time()
                response2 = await rag_service.generate_response(
                    query="Reranking test query",
                    workspace_id="ws_1",
                    config=config_with_rerank
                )
                with_rerank_time = time.time() - start_time
                
                # Both should succeed
                assert response1.answer == "Reranking test response"
                assert response2.answer == "Reranking test response"
                
                print(f"Without reranking: {no_rerank_time:.3f}s")
                print(f"With reranking: {with_rerank_time:.3f}s")
                print(f"Reranking overhead: {((with_rerank_time - no_rerank_time) / no_rerank_time * 100):.1f}%")
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self, rag_service, performance_config):
        """Test streaming response performance"""
        streaming_config = RAGConfig(
            stream_response=True,
            response_style=ResponseStyle.CONVERSATIONAL,
            max_context_length=4000
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service, '_generate_streaming_response') as mock_stream:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Streaming test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                from app.schemas.rag import RAGQueryResponse
                mock_stream.return_value = RAGQueryResponse(
                    answer="Streaming test response",
                    sources=[],
                    response_time_ms=100
                )
                
                start_time = time.time()
                response = await rag_service.generate_response(
                    query="Streaming test query",
                    workspace_id="ws_1",
                    config=streaming_config
                )
                streaming_time = time.time() - start_time
                
                assert response.answer == "Streaming test response"
                assert streaming_time < 1.0  # Should be fast
                
                print(f"Streaming response time: {streaming_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_parallel_processing_performance(self, rag_service, performance_config):
        """Test parallel processing performance"""
        # Test with parallel processing enabled
        parallel_config = RAGConfig(
            parallel_processing=True,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Test with parallel processing disabled
        sequential_config = RAGConfig(
            parallel_processing=False,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    from app.services.production_rag_system import TextBlock
                    mock_text_blocks = [
                        TextBlock(content=f"Parallel test content {i}", metadata={"page": i})
                        for i in range(100)
                    ]
                    mock_process.return_value = mock_text_blocks
                    
                    from app.services.production_rag_system import Chunk
                    mock_chunks = [
                        Chunk(id=f"chunk_{i}", content=f"Parallel chunk {i}", metadata={"document_id": "doc_1"})
                        for i in range(100)
                    ]
                    rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                    mock_add.return_value = True
                    mock_save.return_value = "doc_parallel"
                    
                    # Test parallel processing
                    start_time = time.time()
                    result1 = await rag_service.process_file(
                        file_path="parallel_test.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1",
                        config=parallel_config
                    )
                    parallel_time = time.time() - start_time
                    
                    # Test sequential processing
                    start_time = time.time()
                    result2 = await rag_service.process_file(
                        file_path="sequential_test.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1",
                        config=sequential_config
                    )
                    sequential_time = time.time() - start_time
                    
                    # Both should succeed
                    assert result1["status"] == "success"
                    assert result2["status"] == "success"
                    
                    print(f"Parallel processing time: {parallel_time:.3f}s")
                    print(f"Sequential processing time: {sequential_time:.3f}s")
                    print(f"Parallel processing improvement: {((sequential_time - parallel_time) / sequential_time * 100):.1f}%")
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, rag_service, performance_config):
        """Test performance metrics tracking accuracy"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Metrics test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Metrics test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Get initial metrics
                initial_stats = rag_service.get_performance_stats()
                initial_queries = initial_stats["total_queries"]
                
                # Perform multiple queries
                for i in range(10):
                    await rag_service.generate_response(
                        query=f"Metrics test query {i}",
                        workspace_id="ws_1",
                        config=performance_config
                    )
                
                # Check updated metrics
                updated_stats = rag_service.get_performance_stats()
                assert updated_stats["total_queries"] == initial_queries + 10
                assert updated_stats["avg_query_time"] > 0
                assert updated_stats["success_rate"] > 0
                
                print(f"Total queries: {updated_stats['total_queries']}")
                print(f"Average query time: {updated_stats['avg_query_time']:.3f}s")
                print(f"Success rate: {updated_stats['success_rate']:.2%}")
    
    @pytest.mark.asyncio
    async def test_large_context_handling(self, rag_service, performance_config):
        """Test handling of large context windows"""
        large_context_config = RAGConfig(
            max_context_length=8000,  # Large context window
            top_k=20,  # More results
            similarity_threshold=0.6  # Lower threshold for more results
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                # Mock many search results
                mock_search_results = [
                    SearchResult(
                        id=f"result_{i}",
                        content=f"Large context content {i} " * 100,  # Large content per result
                        score=0.9 - (i * 0.01),
                        metadata={"document_id": f"doc_{i}"}
                    )
                    for i in range(20)
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Large context response",
                    "sources_used": [],
                    "tokens_used": 2000
                }
                
                start_time = time.time()
                response = await rag_service.generate_response(
                    query="Large context test query",
                    workspace_id="ws_1",
                    config=large_context_config
                )
                large_context_time = time.time() - start_time
                
                assert response.answer == "Large context response"
                assert large_context_time < 3.0  # Should handle large context efficiently
                
                print(f"Large context processing time: {large_context_time:.3f}s")
                print(f"Context length: {large_context_config.max_context_length}")
                print(f"Number of results: {len(mock_search_results)}")


class TestProductionRAGScalability:
    """Scalability tests for Production RAG Service"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.mark.asyncio
    async def test_high_volume_query_processing(self, rag_service):
        """Test high volume query processing"""
        config = RAGConfig(
            use_cache=True,
            parallel_processing=True,
            top_k=10,
            similarity_threshold=0.7
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="High volume test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "High volume test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Test with high volume of queries
                start_time = time.time()
                tasks = []
                for i in range(500):  # 500 queries
                    task = rag_service.generate_response(
                        query=f"High volume query {i}",
                        workspace_id="ws_1",
                        config=config
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 500
                assert all(result.answer == "High volume test response" for result in results)
                
                # Should complete in reasonable time
                total_time = end_time - start_time
                assert total_time < 30.0  # Should complete within 30 seconds
                
                print(f"500 queries completed in {total_time:.3f}s")
                print(f"Queries per second: {500/total_time:.1f}")
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_under_load(self, rag_service):
        """Test memory efficiency under high load"""
        config = RAGConfig(
            use_cache=True,
            parallel_processing=True,
            max_context_length=4000
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Memory efficiency test content " * 1000,  # Large content
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Memory efficiency test response " * 100,  # Large response
                    "sources_used": [],
                    "tokens_used": 1000
                }
                
                # Test memory efficiency with many concurrent queries
                start_time = time.time()
                tasks = []
                for i in range(200):  # 200 concurrent queries with large content
                    task = rag_service.generate_response(
                        query=f"Memory efficiency query {i}",
                        workspace_id="ws_1",
                        config=config
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 200
                assert all("Memory efficiency test response" in result.answer for result in results)
                
                # Should complete without memory issues
                total_time = end_time - start_time
                assert total_time < 60.0  # Should complete within 60 seconds
                
                print(f"200 memory-intensive queries completed in {total_time:.3f}s")
                print(f"Memory efficiency: {200/total_time:.1f} queries/second")
