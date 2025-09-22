"""
Enhanced file processing service with advanced text extraction and semantic chunking
"""

import os
import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import PyPDF2
import pandas as pd
from docx import Document as DocxDocument
import structlog
from dataclasses import dataclass
from enum import Enum

# Advanced PDF processing
try:
    import pymupdf as fitz  # PyMuPDF for better PDF processing
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Advanced text processing
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = structlog.get_logger()


class ChunkingStrategy(Enum):
    """Chunking strategies for different content types"""
    SEMANTIC = "semantic"  # Semantic chunking based on meaning
    FIXED_SIZE = "fixed_size"  # Fixed character/token size
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking


@dataclass
class TextBlock:
    """Represents a text block with metadata"""
    text: str
    metadata: Dict[str, Any]
    block_type: str  # 'title', 'paragraph', 'list', 'table', 'code'
    page_number: Optional[int] = None
    section: Optional[str] = None
    importance_score: float = 0.0


class EnhancedFileProcessor:
    """Enhanced file processor with advanced text extraction and semantic chunking"""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        
        # Initialize NLTK if available
        if NLTK_AVAILABLE:
            self._initialize_nltk()
    
    def _initialize_nltk(self):
        """Initialize NLTK resources"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            logger.warning("Failed to initialize NLTK", error=str(e))
            self.stop_words = set()
    
    async def process_file(self, file_path: str, content_type: str) -> List[TextBlock]:
        """
        Process file and extract text blocks with enhanced metadata
        
        Args:
            file_path: Path to the file
            content_type: MIME type of the file
            
        Returns:
            List of TextBlock objects with enhanced metadata
        """
        try:
            logger.info("Processing file", file_path=file_path, content_type=content_type)
            
            if content_type == "application/pdf":
                return await self._process_pdf_enhanced(file_path)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return await self._process_docx_enhanced(file_path)
            elif content_type == "text/csv":
                return await self._process_csv_enhanced(file_path)
            elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                return await self._process_xlsx_enhanced(file_path)
            elif content_type == "text/plain":
                return await self._process_txt_enhanced(file_path)
            elif content_type == "text/markdown":
                return await self._process_markdown_enhanced(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error("File processing failed", error=str(e), file_path=file_path)
            raise
    
    async def _process_pdf_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced PDF processing with better text extraction"""
        text_blocks = []
        
        try:
            if PYMUPDF_AVAILABLE:
                # Use PyMuPDF for better PDF processing
                doc = fitz.open(file_path)
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Extract text with layout information
                    text_dict = page.get_text("dict")
                    
                    # Process text blocks
                    for block in text_dict["blocks"]:
                        if "lines" in block:  # Text block
                            block_text = ""
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    block_text += span["text"] + " "
                            
                            if block_text.strip():
                                # Determine block type based on formatting
                                block_type = self._classify_text_block(block_text)
                                
                                # Calculate importance score
                                importance = self._calculate_importance_score(block_text, block_type)
                                
                                text_blocks.append(TextBlock(
                                    text=block_text.strip(),
                                    metadata={
                                        "page_number": page_num + 1,
                                        "font_size": block["lines"][0]["spans"][0]["size"] if block["lines"] else 12,
                                        "font_flags": block["lines"][0]["spans"][0]["flags"] if block["lines"] else 0,
                                        "bbox": block["bbox"]
                                    },
                                    block_type=block_type,
                                    page_number=page_num + 1,
                                    importance_score=importance
                                ))
                
                doc.close()
            else:
                # Fallback to PyPDF2
                text_blocks = await self._process_pdf_basic(file_path)
                
        except Exception as e:
            logger.error("Enhanced PDF processing failed, falling back to basic", error=str(e))
            text_blocks = await self._process_pdf_basic(file_path)
        
        return text_blocks
    
    async def _process_pdf_basic(self, file_path: str) -> List[TextBlock]:
        """Basic PDF processing fallback"""
        text_blocks = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    # Split into paragraphs
                    paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                    
                    for para in paragraphs:
                        block_type = self._classify_text_block(para)
                        importance = self._calculate_importance_score(para, block_type)
                        
                        text_blocks.append(TextBlock(
                            text=para,
                            metadata={"page_number": page_num + 1},
                            block_type=block_type,
                            page_number=page_num + 1,
                            importance_score=importance
                        ))
        
        return text_blocks
    
    async def _process_docx_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced DOCX processing with structure detection"""
        text_blocks = []
        doc = DocxDocument(file_path)
        
        current_section = None
        
        for paragraph in doc.paragraphs:
            if not paragraph.text.strip():
                continue
            
            # Detect headings and sections
            if paragraph.style.name.startswith('Heading'):
                current_section = paragraph.text.strip()
                block_type = 'title'
                importance = 0.9
            else:
                block_type = 'paragraph'
                importance = self._calculate_importance_score(paragraph.text, block_type)
            
            text_blocks.append(TextBlock(
                text=paragraph.text.strip(),
                metadata={
                    "style": paragraph.style.name,
                    "section": current_section
                },
                block_type=block_type,
                section=current_section,
                importance_score=importance
            ))
        
        return text_blocks
    
    async def _process_csv_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced CSV processing with better data interpretation"""
        text_blocks = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Process each row as a text block
            for idx, row in df.iterrows():
                # Create a readable text representation
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                
                if row_text.strip():
                    text_blocks.append(TextBlock(
                        text=row_text,
                        metadata={
                            "row_index": idx,
                            "columns": list(df.columns),
                            "data_type": "tabular"
                        },
                        block_type="table_row",
                        importance_score=0.7
                    ))
            
            # Add summary information
            summary_text = f"CSV Summary: {len(df)} rows, {len(df.columns)} columns. Columns: {', '.join(df.columns)}"
            text_blocks.append(TextBlock(
                text=summary_text,
                metadata={"data_type": "summary"},
                block_type="summary",
                importance_score=0.8
            ))
            
        except Exception as e:
            logger.error("CSV processing failed", error=str(e))
            raise
        
        return text_blocks
    
    async def _process_xlsx_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced XLSX processing"""
        text_blocks = []
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Process each row
                for idx, row in df.iterrows():
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                    
                    if row_text.strip():
                        text_blocks.append(TextBlock(
                            text=row_text,
                            metadata={
                                "sheet_name": sheet_name,
                                "row_index": idx,
                                "columns": list(df.columns)
                            },
                            block_type="table_row",
                            importance_score=0.7
                        ))
                
                # Add sheet summary
                sheet_summary = f"Sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns"
                text_blocks.append(TextBlock(
                    text=sheet_summary,
                    metadata={"sheet_name": sheet_name, "data_type": "summary"},
                    block_type="summary",
                    importance_score=0.8
                ))
                
        except Exception as e:
            logger.error("XLSX processing failed", error=str(e))
            raise
        
        return text_blocks
    
    async def _process_txt_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced text file processing"""
        text_blocks = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            for para in paragraphs:
                block_type = self._classify_text_block(para)
                importance = self._calculate_importance_score(para, block_type)
                
                text_blocks.append(TextBlock(
                    text=para,
                    metadata={"file_type": "text"},
                    block_type=block_type,
                    importance_score=importance
                ))
        
        return text_blocks
    
    async def _process_markdown_enhanced(self, file_path: str) -> List[TextBlock]:
        """Enhanced Markdown processing with structure detection"""
        text_blocks = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Split by headers and process sections
            sections = re.split(r'\n(#{1,6}\s)', content)
            
            current_section = None
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                if section.startswith('#'):
                    # This is a header
                    current_section = section.strip()
                    block_type = 'title'
                    importance = 0.9
                else:
                    # This is content
                    block_type = 'paragraph'
                    importance = self._calculate_importance_score(section, block_type)
                
                text_blocks.append(TextBlock(
                    text=section.strip(),
                    metadata={"section": current_section, "file_type": "markdown"},
                    block_type=block_type,
                    section=current_section,
                    importance_score=importance
                ))
        
        return text_blocks
    
    def _classify_text_block(self, text: str) -> str:
        """Classify text block type based on content"""
        text_lower = text.lower().strip()
        
        # Check for titles/headings
        if (text.startswith('#') or 
            len(text) < 100 and text.isupper() or
            re.match(r'^[A-Z][^.!?]*$', text)):
            return 'title'
        
        # Check for lists
        if (text.startswith(('•', '-', '*', '1.', '2.', '3.')) or
            re.match(r'^\d+\.\s', text)):
            return 'list'
        
        # Check for code
        if ('```' in text or 
            text.startswith('    ') or
            re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*[=\(]', text)):
            return 'code'
        
        # Check for tables (basic detection)
        if '|' in text and text.count('|') > 2:
            return 'table'
        
        return 'paragraph'
    
    def _calculate_importance_score(self, text: str, block_type: str) -> float:
        """Calculate importance score for text block"""
        base_scores = {
            'title': 0.9,
            'summary': 0.8,
            'list': 0.7,
            'table': 0.6,
            'paragraph': 0.5,
            'code': 0.4
        }
        
        base_score = base_scores.get(block_type, 0.5)
        
        # Adjust based on content characteristics
        text_lower = text.lower()
        
        # Boost for important keywords
        important_keywords = [
            'important', 'critical', 'key', 'main', 'primary', 'essential',
            'summary', 'conclusion', 'overview', 'introduction'
        ]
        
        keyword_boost = sum(0.1 for keyword in important_keywords if keyword in text_lower)
        
        # Boost for length (more content = more important)
        length_boost = min(0.2, len(text) / 1000)
        
        # Boost for numbers and data
        data_boost = 0.1 if re.search(r'\d+', text) else 0
        
        final_score = min(1.0, base_score + keyword_boost + length_boost + data_boost)
        
        return round(final_score, 2)
    
    def create_semantic_chunks(self, text_blocks: List[TextBlock]) -> List[Dict[str, Any]]:
        """Create semantic chunks from text blocks"""
        chunks = []
        
        if self.chunking_strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._create_semantic_chunks(text_blocks)
        elif self.chunking_strategy == ChunkingStrategy.SENTENCE:
            chunks = self._create_sentence_chunks(text_blocks)
        elif self.chunking_strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._create_paragraph_chunks(text_blocks)
        else:  # FIXED_SIZE
            chunks = self._create_fixed_size_chunks(text_blocks)
        
        return chunks
    
    def _create_semantic_chunks(self, text_blocks: List[TextBlock]) -> List[Dict[str, Any]]:
        """Create semantic chunks based on content meaning and structure"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for block in text_blocks:
            block_size = len(block.text)
            
            # If adding this block would exceed size limit and we have content
            if current_size + block_size > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk_text = " ".join([b.text for b in current_chunk])
                chunk_metadata = self._create_chunk_metadata(current_chunk, len(chunks))
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
                # Start new chunk with overlap
                overlap_blocks = self._get_overlap_blocks(current_chunk)
                current_chunk = overlap_blocks + [block]
                current_size = sum(len(b.text) for b in current_chunk)
            else:
                current_chunk.append(block)
                current_size += block_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join([b.text for b in current_chunk])
            chunk_metadata = self._create_chunk_metadata(current_chunk, len(chunks))
            chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def _create_sentence_chunks(self, text_blocks: List[TextBlock]) -> List[Dict[str, Any]]:
        """Create chunks based on sentences"""
        chunks = []
        
        for block in text_blocks:
            if NLTK_AVAILABLE:
                sentences = sent_tokenize(block.text)
            else:
                # Simple sentence splitting
                sentences = re.split(r'[.!?]+', block.text)
                sentences = [s.strip() for s in sentences if s.strip()]
            
            current_chunk = []
            current_size = 0
            
            for sentence in sentences:
                sentence_size = len(sentence)
                
                if current_size + sentence_size > self.chunk_size and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_metadata = self._create_chunk_metadata([block], len(chunks))
                    chunks.append({
                        "text": chunk_text,
                        "metadata": chunk_metadata
                    })
                    
                    # Start new chunk with overlap
                    overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                    current_chunk = overlap_sentences + [sentence]
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk.append(sentence)
                    current_size += sentence_size
            
            # Add final chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_metadata = self._create_chunk_metadata([block], len(chunks))
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
        
        return chunks
    
    def _create_paragraph_chunks(self, text_blocks: List[TextBlock]) -> List[Dict[str, Any]]:
        """Create chunks based on paragraphs"""
        chunks = []
        
        for block in text_blocks:
            chunk_metadata = self._create_chunk_metadata([block], len(chunks))
            chunks.append({
                "text": block.text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def _create_fixed_size_chunks(self, text_blocks: List[TextBlock]) -> List[Dict[str, Any]]:
        """Create fixed-size chunks"""
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for block in text_blocks:
            if current_size + len(block.text) > self.chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": {"chunk_type": "fixed_size", "chunk_index": len(chunks)}
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + " " + block.text if overlap_text else block.text
                current_size = len(current_chunk)
            else:
                current_chunk += " " + block.text if current_chunk else block.text
                current_size = len(current_chunk)
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": {"chunk_type": "fixed_size", "chunk_index": len(chunks)}
            })
        
        return chunks
    
    def _get_overlap_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """Get blocks for overlap in next chunk"""
        if len(blocks) <= 1:
            return []
        
        # Take last 1-2 blocks for overlap
        overlap_count = min(2, len(blocks))
        return blocks[-overlap_count:]
    
    def _create_chunk_metadata(self, blocks: List[TextBlock], chunk_index: int) -> Dict[str, Any]:
        """Create metadata for a chunk"""
        metadata = {
            "chunk_index": chunk_index,
            "chunk_type": self.chunking_strategy.value,
            "block_count": len(blocks),
            "total_length": sum(len(block.text) for block in blocks),
            "avg_importance": sum(block.importance_score for block in blocks) / len(blocks) if blocks else 0,
            "block_types": [block.block_type for block in blocks],
            "sections": list(set(block.section for block in blocks if block.section)),
            "page_numbers": list(set(block.page_number for block in blocks if block.page_number))
        }
        
        # Add metadata from blocks
        for block in blocks:
            metadata.update(block.metadata)
        
        return metadata


# Global instance
enhanced_file_processor = EnhancedFileProcessor()
