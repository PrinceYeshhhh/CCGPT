"""
File processing service for extracting text from various file formats
"""

import os
import hashlib
import re
from typing import List, Dict, Any
import pypdf
import pandas as pd
from docx import Document as DocxDocument
import structlog

logger = structlog.get_logger()


class FileProcessor:
    """File processor for extracting text from various formats"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from file based on type"""
        try:
            if file_type == "pdf":
                return self._extract_pdf_text(file_path)
            elif file_type == "docx":
                return self._extract_docx_text(file_path)
            elif file_type == "csv":
                return self._extract_csv_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(
                "Text extraction failed",
                error=str(e),
                file_path=file_path,
                file_type=file_type
            )
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        except Exception as e:
            logger.error("PDF text extraction failed", error=str(e), file_path=file_path)
            raise
        return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error("DOCX text extraction failed", error=str(e), file_path=file_path)
            raise
    
    def _extract_csv_text(self, file_path: str) -> str:
        """Extract text from CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Convert to text format
            text = ""
            for index, row in df.iterrows():
                # Create Q&A pairs from CSV
                for column in df.columns:
                    if pd.notna(row[column]) and str(row[column]).strip():
                        text += f"Q: {column}\nA: {row[column]}\n\n"
            
            return text
        except Exception as e:
            logger.error("CSV text extraction failed", error=str(e), file_path=file_path)
            raise
    
    def create_chunks(self, text: str, document_id: int) -> List[Dict[str, Any]]:
        """Split text into chunks for processing"""
        if not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        # Create chunks
        chunks = []
        current_chunk = ""
        current_chunk_index = 0
        word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = self._create_chunk_data(
                    current_chunk, current_chunk_index, document_id, word_count
                )
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_chunk_index += 1
                word_count = len(current_chunk.split())
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                word_count = len(current_chunk.split())
        
        # Add final chunk
        if current_chunk.strip():
            chunk_data = self._create_chunk_data(
                current_chunk, current_chunk_index, document_id, word_count
            )
            chunks.append(chunk_data)
        
        logger.info(
            "Text chunked successfully",
            document_id=document_id,
            total_chunks=len(chunks),
            total_words=sum(chunk["word_count"] for chunk in chunks)
        )
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLP libraries)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        words = text.split()
        if len(words) <= self.chunk_overlap // 10:  # Approximate word count
            return text
        
        # Return last portion of text for overlap
        overlap_words = words[-(self.chunk_overlap // 10):]
        return " ".join(overlap_words)
    
    def _create_chunk_data(
        self, 
        content: str, 
        chunk_index: int, 
        document_id: int, 
        word_count: int
    ) -> Dict[str, Any]:
        """Create chunk data dictionary"""
        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Extract section title (first line or first sentence)
        section_title = None
        lines = content.split('\n')
        if lines and lines[0].strip():
            section_title = lines[0].strip()[:100]  # Limit length
        
        return {
            "index": chunk_index,
            "content": content.strip(),
            "hash": content_hash,
            "word_count": word_count,
            "section_title": section_title,
            "page_number": None  # Can be enhanced to track page numbers
        }
