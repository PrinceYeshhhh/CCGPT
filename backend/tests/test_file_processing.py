"""
Tests for file processing functionality
"""

import pytest
import tempfile
import os
from app.utils.file_parser import extract_text_from_file
from app.utils.chunker import chunk_text


class TestFileParser:
    """Test file parsing utilities"""
    
    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        text = "This is a test sentence. This is another test sentence. " * 100
        chunks = chunk_text(text, max_tokens=50, overlap_tokens=10)
        
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        chunks = chunk_text("")
        assert chunks == []
    
    def test_chunk_text_short(self):
        """Test chunking short text"""
        text = "Short text"
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == "Short text"


class TestChunker:
    """Test chunking utilities"""
    
    def test_estimate_tokens(self):
        """Test token estimation"""
        from app.utils.chunker import _estimate_tokens
        
        text = "This is a test sentence with multiple words"
        tokens = _estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_clean_text(self):
        """Test text cleaning"""
        from app.utils.chunker import _clean_text
        
        dirty_text = "  This   has   extra   spaces  \n\n\n  "
        clean_text = _clean_text(dirty_text)
        assert clean_text == "This has extra spaces"
    
    def test_split_sentences(self):
        """Test sentence splitting"""
        from app.utils.chunker import _split_into_sentences
        
        text = "First sentence. Second sentence! Third sentence?"
        sentences = _split_into_sentences(text)
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]


if __name__ == "__main__":
    pytest.main([__file__])
