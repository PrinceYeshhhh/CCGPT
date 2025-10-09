"""
Unit tests for Production RAG System
Tests the core production RAG functionality with comprehensive coverage
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import tempfile
import os

from app.services.production_rag_system import (
    ProductionFileProcessor,
    FileType,
    ChunkingStrategy,
    RetrievalStrategy,
    RerankingMethod,
    TextBlock,
    Chunk,
    RetrievalResult
)

class TestProductionFileProcessor:
    """Unit tests for ProductionFileProcessor"""
    
    @pytest.fixture
    def file_processor(self):
        """Create a file processor instance for testing"""
        return ProductionFileProcessor(
            chunk_size=1000,
            chunk_overlap=200,
            chunking_strategy=ChunkingStrategy.SEMANTIC
        )
    
    def test_initialization(self, file_processor):
        """Test file processor initialization"""
        assert file_processor.chunk_size == 1000
        assert file_processor.chunk_overlap == 200
        assert file_processor.chunking_strategy == ChunkingStrategy.SEMANTIC
    
    def test_text_processing_initialization(self, file_processor):
        """Test text processing tools initialization"""
        # In testing mode, text processing should be disabled
        assert hasattr(file_processor, 'text_processing_available')
    
    def test_ml_models_initialization(self, file_processor):
        """Test ML models initialization"""
        # In testing mode, ML models should be disabled
        assert hasattr(file_processor, 'ml_available')
    
    @pytest.mark.asyncio
    async def test_process_pdf_file(self, file_processor):
        """Test PDF file processing"""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF")
            temp_file_path = temp_file.name
        
        try:
            # Mock PyPDF2 to avoid actual PDF processing
            with patch('app.services.production_rag_system.PyPDF2.PdfReader') as mock_reader:
                mock_page = Mock()
                mock_page.extract_text.return_value = "Test PDF content for processing"
                mock_reader.return_value.pages = [mock_page]
                
                result = await file_processor.process_file(temp_file_path, "application/pdf")
                
                assert isinstance(result, list)
                assert len(result) > 0
                assert all(isinstance(block, TextBlock) for block in result)
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_process_txt_file(self, file_processor):
        """Test text file processing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a test text file with multiple sentences. It contains content that should be processed and chunked appropriately for the RAG system.")
            temp_file_path = temp_file.name
        
        try:
            result = await file_processor.process_file(temp_file_path, "text/plain")
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(block, TextBlock) for block in result)
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_process_unsupported_file_type(self, file_processor):
        """Test processing of unsupported file types"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_file:
            temp_file.write(b"Some binary content")
            temp_file_path = temp_file.name
        
        try:
            result = await file_processor.process_file(temp_file_path, "application/unknown")
            
            # Should return empty list for unsupported file types
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            os.unlink(temp_file_path)
    
    def test_create_semantic_chunks(self, file_processor):
        """Test semantic chunking functionality"""
        text_blocks = [
            TextBlock(
                content="This is the first paragraph about machine learning.",
                metadata={"source": "doc1", "page": 1}
            ),
            TextBlock(
                content="This is the second paragraph about artificial intelligence.",
                metadata={"source": "doc1", "page": 1}
            ),
            TextBlock(
                content="This is the third paragraph about natural language processing.",
                metadata={"source": "doc1", "page": 2}
            )
        ]
        
        chunks = file_processor.create_semantic_chunks(text_blocks)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
    
    def test_create_semantic_chunks_empty_input(self, file_processor):
        """Test semantic chunking with empty input"""
        chunks = file_processor.create_semantic_chunks([])
        
        assert isinstance(chunks, list)
        assert len(chunks) == 0
    
    def test_chunk_text_semantic_strategy(self, file_processor):
        """Test text chunking with semantic strategy"""
        text = "This is a long text that should be chunked semantically. " * 50
        
        chunks = file_processor.chunk_text(text, chunking_strategy=ChunkingStrategy.SEMANTIC)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
    
    def test_chunk_text_fixed_strategy(self, file_processor):
        """Test text chunking with fixed strategy"""
        text = "This is a long text that should be chunked with fixed size. " * 50
        
        chunks = file_processor.chunk_text(text, chunking_strategy=ChunkingStrategy.FIXED)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
    
    def test_extract_keywords(self, file_processor):
        """Test keyword extraction"""
        text = "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models."
        
        keywords = file_processor.extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert all(isinstance(keyword, str) for keyword in keywords)
    
    def test_extract_keywords_empty_text(self, file_processor):
        """Test keyword extraction with empty text"""
        keywords = file_processor.extract_keywords("")
        
        assert isinstance(keywords, list)
        assert len(keywords) == 0
    
    def test_clean_text(self, file_processor):
        """Test text cleaning functionality"""
        dirty_text = "This is a   text with   multiple    spaces and\n\nnewlines."
        
        cleaned_text = file_processor.clean_text(dirty_text)
        
        assert isinstance(cleaned_text, str)
        assert "   " not in cleaned_text
        assert "\n\n" not in cleaned_text
    
    def test_clean_text_special_characters(self, file_processor):
        """Test text cleaning with special characters"""
        text_with_special = "This text has special chars: @#$%^&*()_+{}|:<>?[]\\;'\",./"
        
        cleaned_text = file_processor.clean_text(text_with_special)
        
        assert isinstance(cleaned_text, str)
        # Should preserve most characters but clean formatting
    
    def test_detect_language(self, file_processor):
        """Test language detection"""
        english_text = "This is an English text for language detection."
        spanish_text = "Este es un texto en español para detección de idioma."
        
        # Test English detection
        lang = file_processor.detect_language(english_text)
        assert isinstance(lang, str)
        
        # Test Spanish detection
        lang = file_processor.detect_language(spanish_text)
        assert isinstance(lang, str)
    
    def test_detect_language_empty_text(self, file_processor):
        """Test language detection with empty text"""
        lang = file_processor.detect_language("")
        
        assert isinstance(lang, str)
        assert lang == "unknown" or lang == "en"  # Default fallback
    
    def test_get_file_type(self, file_processor):
        """Test file type detection"""
        # Test PDF
        file_type = file_processor.get_file_type("test.pdf")
        assert file_type == FileType.PDF
        
        # Test TXT
        file_type = file_processor.get_file_type("test.txt")
        assert file_type == FileType.TEXT
        
        # Test DOCX
        file_type = file_processor.get_file_type("test.docx")
        assert file_type == FileType.DOCX
        
        # Test unknown
        file_type = file_processor.get_file_type("test.xyz")
        assert file_type == FileType.UNKNOWN
    
    def test_validate_file_size(self, file_processor):
        """Test file size validation"""
        # Test valid size
        is_valid = file_processor.validate_file_size(1024 * 1024)  # 1MB
        assert is_valid is True
        
        # Test too large
        is_valid = file_processor.validate_file_size(100 * 1024 * 1024)  # 100MB
        assert is_valid is False
    
    def test_validate_file_type(self, file_processor):
        """Test file type validation"""
        # Test valid types
        assert file_processor.validate_file_type("application/pdf") is True
        assert file_processor.validate_file_type("text/plain") is True
        assert file_processor.validate_file_type("application/vnd.openxmlformats-officedocument.wordprocessingml.document") is True
        
        # Test invalid types
        assert file_processor.validate_file_type("application/unknown") is False
        assert file_processor.validate_file_type("image/jpeg") is False

class TestTextBlock:
    """Unit tests for TextBlock class"""
    
    def test_text_block_creation(self):
        """Test TextBlock creation"""
        block = TextBlock(
            content="Test content",
            metadata={"source": "doc1", "page": 1}
        )
        
        assert block.content == "Test content"
        assert block.metadata == {"source": "doc1", "page": 1}
        assert block.id is not None
        assert isinstance(block.created_at, datetime)
    
    def test_text_block_without_metadata(self):
        """Test TextBlock creation without metadata"""
        block = TextBlock(content="Test content")
        
        assert block.content == "Test content"
        assert block.metadata == {}
        assert block.id is not None

class TestChunk:
    """Unit tests for Chunk class"""
    
    def test_chunk_creation(self):
        """Test Chunk creation"""
        chunk = Chunk(
            content="Test chunk content",
            metadata={"source": "doc1", "chunk_index": 0},
            chunk_id="chunk_123"
        )
        
        assert chunk.content == "Test chunk content"
        assert chunk.metadata == {"source": "doc1", "chunk_index": 0}
        assert chunk.chunk_id == "chunk_123"
        assert chunk.id is not None
        assert isinstance(chunk.created_at, datetime)
    
    def test_chunk_without_chunk_id(self):
        """Test Chunk creation without chunk_id"""
        chunk = Chunk(
            content="Test chunk content",
            metadata={"source": "doc1"}
        )
        
        assert chunk.content == "Test chunk content"
        assert chunk.chunk_id is not None  # Should be auto-generated

class TestRetrievalResult:
    """Unit tests for RetrievalResult class"""
    
    def test_retrieval_result_creation(self):
        """Test RetrievalResult creation"""
        result = RetrievalResult(
            chunk_id="chunk_123",
            content="Retrieved content",
            score=0.95,
            metadata={"source": "doc1"}
        )
        
        assert result.chunk_id == "chunk_123"
        assert result.content == "Retrieved content"
        assert result.score == 0.95
        assert result.metadata == {"source": "doc1"}
        assert result.reranked_score is None
    
    def test_retrieval_result_with_reranking(self):
        """Test RetrievalResult with reranking"""
        result = RetrievalResult(
            chunk_id="chunk_123",
            content="Retrieved content",
            score=0.95,
            metadata={"source": "doc1"},
            reranked_score=0.98
        )
        
        assert result.reranked_score == 0.98

class TestEnums:
    """Unit tests for enum classes"""
    
    def test_file_type_enum(self):
        """Test FileType enum values"""
        assert FileType.PDF.value == "pdf"
        assert FileType.TEXT.value == "text"
        assert FileType.DOCX.value == "docx"
        assert FileType.UNKNOWN.value == "unknown"
    
    def test_chunking_strategy_enum(self):
        """Test ChunkingStrategy enum values"""
        assert ChunkingStrategy.FIXED.value == "fixed"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.SENTENCE.value == "sentence"
    
    def test_retrieval_strategy_enum(self):
        """Test RetrievalStrategy enum values"""
        assert RetrievalStrategy.SIMILARITY.value == "similarity"
        assert RetrievalStrategy.HYBRID.value == "hybrid"
        assert RetrievalStrategy.KEYWORD.value == "keyword"
    
    def test_reranking_method_enum(self):
        """Test RerankingMethod enum values"""
        assert RerankingMethod.CROSS_ENCODER.value == "cross_encoder"
        assert RerankingMethod.BM25.value == "bm25"
        assert RerankingMethod.NONE.value == "none"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

