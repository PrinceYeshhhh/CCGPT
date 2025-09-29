"""
Advanced semantic chunking service with multiple strategies
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from app.core.config import settings
from app.exceptions import DocumentProcessingError

logger = structlog.get_logger()


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    SECTION_BASED = "section_based"
    HYBRID = "hybrid"


@dataclass
class Chunk:
    """Represents a document chunk"""
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    importance_score: float = 0.0
    chunk_id: str = ""
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = f"chunk_{self.chunk_index}_{hashlib.md5(self.content.encode()).hexdigest()[:8]}"


class SemanticChunkingService:
    """Advanced semantic chunking service with multiple strategies"""
    
    def __init__(self):
        self.sentence_endings = re.compile(r'[.!?]+')
        self.paragraph_separators = re.compile(r'\n\s*\n')
        self.section_headers = re.compile(r'^(#{1,6}\s+.+|\d+\.\s+.+|[A-Z][A-Z\s]+:?\s*$)', re.MULTILINE)
    
    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ) -> List[Chunk]:
        """Chunk text using the specified strategy"""
        try:
            if not text or not text.strip():
                return []
            
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Choose chunking strategy
            if strategy == ChunkingStrategy.FIXED_SIZE:
                chunks = self._fixed_size_chunking(cleaned_text, chunk_size, chunk_overlap)
            elif strategy == ChunkingStrategy.SEMANTIC:
                chunks = self._semantic_chunking(cleaned_text, chunk_size, chunk_overlap)
            elif strategy == ChunkingStrategy.SENTENCE_BASED:
                chunks = self._sentence_based_chunking(cleaned_text, chunk_size, chunk_overlap)
            elif strategy == ChunkingStrategy.PARAGRAPH_BASED:
                chunks = self._paragraph_based_chunking(cleaned_text, chunk_size, chunk_overlap)
            elif strategy == ChunkingStrategy.SECTION_BASED:
                chunks = self._section_based_chunking(cleaned_text, chunk_size, chunk_overlap)
            elif strategy == ChunkingStrategy.HYBRID:
                chunks = self._hybrid_chunking(cleaned_text, chunk_size, chunk_overlap)
            else:
                raise ValueError(f"Unknown chunking strategy: {strategy}")
            
            # Post-process chunks
            chunks = self._post_process_chunks(chunks, text)
            
            logger.info(
                "Text chunked successfully",
                strategy=strategy.value,
                original_length=len(text),
                chunks_count=len(chunks),
                avg_chunk_size=sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0
            )
            
            return chunks
            
        except Exception as e:
            logger.error("Chunking failed", error=str(e), strategy=strategy.value)
            raise DocumentProcessingError(
                message="Text chunking failed",
                details={"strategy": strategy.value, "error": str(e)}
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for chunking"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _fixed_size_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Fixed-size chunking strategy"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                # Find last space before end
                last_space = text.rfind(' ', start, end)
                if last_space > start + chunk_size * 0.5:  # Don't make chunks too small
                    end = last_space
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={"strategy": "fixed_size", "size": len(chunk_content)}
                ))
                chunk_index += 1
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def _semantic_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Semantic chunking based on sentence boundaries and content similarity"""
        # First, split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_size + sentence_size > chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_content = ' '.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(chunk_content),
                    metadata={
                        "strategy": "semantic",
                        "sentence_count": len(current_chunk),
                        "size": len(chunk_content)
                    }
                ))
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
                start_char += len(' '.join(overlap_sentences)) + 1
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    "strategy": "semantic",
                    "sentence_count": len(current_chunk),
                    "size": len(chunk_content)
                }
            ))
        
        return chunks
    
    def _sentence_based_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Sentence-based chunking strategy"""
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Finalize current chunk
                chunk_content = ' '.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(chunk_content),
                    metadata={
                        "strategy": "sentence_based",
                        "sentence_count": len(current_chunk),
                        "size": len(chunk_content)
                    }
                ))
                
                # Start new chunk
                current_chunk = [sentence]
                current_size = sentence_size
                start_char += len(chunk_content) + 1
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    "strategy": "sentence_based",
                    "sentence_count": len(current_chunk),
                    "size": len(chunk_content)
                }
            ))
        
        return chunks
    
    def _paragraph_based_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Paragraph-based chunking strategy"""
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            if current_size + paragraph_size > chunk_size and current_chunk:
                # Finalize current chunk
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(chunk_content),
                    metadata={
                        "strategy": "paragraph_based",
                        "paragraph_count": len(current_chunk),
                        "size": len(chunk_content)
                    }
                ))
                
                # Start new chunk
                current_chunk = [paragraph]
                current_size = paragraph_size
                start_char += len(chunk_content) + 2
                chunk_index += 1
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(chunk_content),
                metadata={
                    "strategy": "paragraph_based",
                    "paragraph_count": len(current_chunk),
                    "size": len(chunk_content)
                }
            ))
        
        return chunks
    
    def _section_based_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Section-based chunking strategy"""
        sections = self._split_into_sections(text)
        
        chunks = []
        chunk_index = 0
        start_char = 0
        
        for section in sections:
            section_content = section['content']
            section_title = section['title']
            
            # If section is too large, split it further
            if len(section_content) > chunk_size:
                # Use semantic chunking for large sections
                sub_chunks = self._semantic_chunking(section_content, chunk_size, overlap)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata['section_title'] = section_title
                    sub_chunk.metadata['strategy'] = 'section_based'
                    sub_chunk.chunk_index = chunk_index
                    sub_chunk.start_char += start_char
                    sub_chunk.end_char += start_char
                    chunks.append(sub_chunk)
                    chunk_index += 1
            else:
                chunks.append(Chunk(
                    content=section_content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=start_char + len(section_content),
                    metadata={
                        "strategy": "section_based",
                        "section_title": section_title,
                        "size": len(section_content)
                    }
                ))
                chunk_index += 1
            
            start_char += len(section_content) + 1
        
        return chunks
    
    def _hybrid_chunking(self, text: str, chunk_size: int, overlap: int) -> List[Chunk]:
        """Hybrid chunking combining multiple strategies"""
        # First try section-based
        sections = self._split_into_sections(text)
        
        if len(sections) > 1:
            # Use section-based for documents with clear sections
            return self._section_based_chunking(text, chunk_size, overlap)
        else:
            # Use semantic chunking for documents without clear sections
            return self._semantic_chunking(text, chunk_size, overlap)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = self.sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = self.paragraph_separators.split(text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """Split text into sections based on headers"""
        sections = []
        current_section = {'title': '', 'content': ''}
        
        lines = text.split('\n')
        
        for line in lines:
            if self.section_headers.match(line.strip()):
                # Save previous section
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line.strip(),
                    'content': ''
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _post_process_chunks(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """Post-process chunks to add metadata and calculate importance scores"""
        for chunk in chunks:
            # Calculate importance score based on various factors
            chunk.importance_score = self._calculate_importance_score(chunk, original_text)
            
            # Add word count
            chunk.metadata['word_count'] = len(chunk.content.split())
            
            # Add character count
            chunk.metadata['char_count'] = len(chunk.content)
            
            # Add hash for deduplication
            chunk.metadata['content_hash'] = hashlib.md5(chunk.content.encode()).hexdigest()
        
        return chunks
    
    def _calculate_importance_score(self, chunk: Chunk, original_text: str) -> float:
        """Calculate importance score for a chunk"""
        score = 0.0
        
        # Base score from chunk size (normalized)
        score += min(len(chunk.content) / 1000, 1.0) * 0.2
        
        # Score from section headers
        if 'section_title' in chunk.metadata:
            score += 0.3
        
        # Score from question marks (indicates Q&A content)
        question_count = chunk.content.count('?')
        score += min(question_count * 0.1, 0.2)
        
        # Score from bullet points or numbered lists
        if re.search(r'^[\s]*[•\-\*]\s+', chunk.content, re.MULTILINE):
            score += 0.1
        
        # Score from code blocks or technical content
        if re.search(r'```|`[^`]+`', chunk.content):
            score += 0.1
        
        # Score from URLs or links (indicates external references)
        if re.search(r'https?://', chunk.content):
            score += 0.1
        
        return min(score, 1.0)


# Global chunking service instance
semantic_chunking_service = SemanticChunkingService()
