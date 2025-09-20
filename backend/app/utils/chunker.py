"""
Text chunking utilities with token estimation and overlap
"""

import re
from typing import List, Dict, Any
import structlog
from app.core.config import settings

logger = structlog.get_logger()


def chunk_text(text: str, max_tokens: int = None, overlap_tokens: int = None) -> List[str]:
    """
    Split text into chunks with overlap
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (defaults to settings)
        overlap_tokens: Overlap tokens between chunks (defaults to settings)
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    max_tokens = max_tokens or settings.MAX_CHUNK_TOKENS
    overlap_tokens = overlap_tokens or settings.CHUNK_OVERLAP_TOKENS
    
    # Clean text
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return []
    
    # Split into sentences
    sentences = _split_into_sentences(cleaned_text)
    if not sentences:
        return []
    
    # Create chunks
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Estimate tokens for the sentence
        sentence_tokens = _estimate_tokens(sentence)
        
        # Check if adding this sentence would exceed max tokens
        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            overlap_text = _get_overlap_text(current_chunk, overlap_tokens)
            current_chunk = overlap_text + " " + sentence if overlap_text else sentence
            current_tokens = _estimate_tokens(current_chunk)
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
            current_tokens += sentence_tokens
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    logger.info(
        "Text chunked successfully",
        total_chunks=len(chunks),
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens
    )
    
    return chunks


def _clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters except newlines and tabs
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    
    # Normalize line breaks
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple heuristics"""
    # Simple sentence splitting - can be improved with NLTK
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count for text
    
    Uses a simple approximation: tokens ≈ words / 0.75
    This is a rough estimate - for production, use the actual tokenizer
    """
    if not text:
        return 0
    
    # Count words
    words = len(text.split())
    
    # Rough token estimation (can be improved with actual tokenizer)
    estimated_tokens = int(words / 0.75)
    
    return max(1, estimated_tokens)  # At least 1 token


def _get_overlap_text(text: str, overlap_tokens: int) -> str:
    """Get overlap text from the end of current chunk"""
    if not text or overlap_tokens <= 0:
        return ""
    
    # Split into words
    words = text.split()
    if len(words) <= 1:
        return text
    
    # Calculate how many words to take for overlap
    overlap_words = max(1, int(overlap_tokens * 0.75))  # Convert tokens to words
    overlap_words = min(overlap_words, len(words))
    
    # Return last portion of text for overlap
    return " ".join(words[-overlap_words:])


def create_chunk_metadata(chunk: str, chunk_index: int, source_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create metadata for a chunk"""
    metadata = {
        "chunk_index": chunk_index,
        "char_count": len(chunk),
        "word_count": len(chunk.split()),
        "estimated_tokens": _estimate_tokens(chunk)
    }
    
    # Add source metadata if available
    if source_metadata:
        metadata.update(source_metadata)
    
    return metadata
