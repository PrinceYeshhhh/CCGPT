"""
Production-grade RAG system with unified file processing, chunking, and retrieval
"""

import asyncio
import hashlib
import re
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import structlog
from sqlalchemy.orm import Session

# Core dependencies
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# File processing
import PyPDF2
try:
    import fitz  # PyMuPDF canonical import
except Exception:  # pragma: no cover
    fitz = None
from docx import Document as DocxDocument
import openpyxl
from markdown import markdown
import json

# Advanced text processing
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize, pos_tag
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.chunk import ne_chunk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# ML and embeddings
try:
from sentence_transformers import SentenceTransformer, CrossEncoder
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Vector database
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Redis caching
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document, DocumentChunk
from app.schemas.rag import RAGQueryResponse

logger = structlog.get_logger()


class FileType(Enum):
    """Supported file types"""
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    TXT = "text/plain"
    MD = "text/markdown"
    CSV = "text/csv"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    JSON = "application/json"
    HTML = "text/html"


class ChunkingStrategy(Enum):
    """Advanced chunking strategies"""
    SEMANTIC = "semantic"  # Semantic chunking based on meaning
    FIXED_SIZE = "fixed_size"  # Fixed character/token size
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking
    SLIDING_WINDOW = "sliding_window"  # Sliding window with overlap
    HIERARCHICAL = "hierarchical"  # Hierarchical chunking
    ADAPTIVE = "adaptive"  # Adaptive chunking based on content


class RetrievalStrategy(Enum):
    """Retrieval strategies"""
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"  # Vector + BM25
    MULTI_QUERY = "multi_query"
    RERANKED = "reranked"
    FUSION = "fusion"  # Multiple retrieval methods fused


class RerankingMethod(Enum):
    """Reranking methods"""
    COSINE_SIMILARITY = "cosine_similarity"
    CROSS_ENCODER = "cross_encoder"
    BM25 = "bm25"
    COMBINED = "combined"
    NEURAL = "neural"  # Neural reranking


@dataclass
class TextBlock:
    """Enhanced text block with rich metadata"""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    block_type: str = "paragraph"
    page_number: Optional[int] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    importance_score: float = 0.0
    semantic_embedding: Optional[List[float]] = None
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    language: str = "en"
    confidence: float = 1.0


@dataclass
class Chunk:
    """Enhanced chunk with comprehensive metadata"""
    text: str
    chunk_id: str
    document_id: int
    workspace_id: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    importance_score: float = 0.0
    semantic_score: float = 0.0
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class RetrievalResult:
    """Enhanced retrieval result"""
    chunk_id: str
    document_id: int
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_method: str = "vector_similarity"
    rank: int = 0
    reranked_score: Optional[float] = None
    explanation: Optional[str] = None


class ProductionFileProcessor:
    """Production-grade file processor with advanced capabilities"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        
        # Initialize text processing
        self._initialize_text_processing()
        
        # Initialize ML models
        self._initialize_ml_models()
    
    def _initialize_text_processing(self):
        """Initialize text processing tools"""
        import os
        if os.getenv("TESTING"):
            # Skip NLTK downloads in CI/testing
            self.text_processing_available = False
            return
        if NLTK_AVAILABLE:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
                nltk.download('wordnet', quiet=True)
                
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
                self.text_processing_available = True
            except Exception as e:
                logger.warning("Failed to initialize NLTK", error=str(e))
                self.text_processing_available = False
        else:
            self.text_processing_available = False
    
    def _initialize_ml_models(self):
        """Initialize ML models for advanced processing"""
        import os
        if os.getenv("TESTING"):
            # Skip heavy model loading in CI/testing
            self.embedding_model = None
            self.reranking_model = None
            self.tfidf_vectorizer = None
            self.ml_available = False
            logger.info("Skipping ML model initialization in TESTING mode")
            return
        if ML_AVAILABLE:
            try:
                # Initialize sentence transformer for embeddings
                self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
                
                # Initialize cross-encoder for reranking
                self.reranking_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                
                # Initialize TF-IDF vectorizer for keyword extraction
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                
                self.ml_available = True
                logger.info("ML models initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize ML models", error=str(e))
                self.ml_available = False
        else:
            self.ml_available = False
    
    async def process_file(self, file_path: str, content_type: str) -> List[TextBlock]:
        """Process file with advanced text extraction and analysis"""
        try:
            logger.info("Processing file", file_path=file_path, content_type=content_type)
            
            # Route to appropriate processor
            if content_type == FileType.PDF.value:
                return await self._process_pdf_advanced(file_path)
            elif content_type == FileType.DOCX.value:
                return await self._process_docx_advanced(file_path)
            elif content_type == FileType.TXT.value:
                return await self._process_txt_advanced(file_path)
            elif content_type == FileType.MD.value:
                return await self._process_markdown_advanced(file_path)
            elif content_type == FileType.CSV.value:
                return await self._process_csv_advanced(file_path)
            elif content_type == FileType.XLSX.value:
                return await self._process_xlsx_advanced(file_path)
            elif content_type == FileType.JSON.value:
                return await self._process_json_advanced(file_path)
            elif content_type == FileType.HTML.value:
                return await self._process_html_advanced(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error("File processing failed", error=str(e), file_path=file_path)
            raise
    
    async def _process_pdf_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced PDF processing with layout analysis"""
        text_blocks = []
        
        try:
            # Use PyMuPDF for better PDF processing
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text with detailed layout information
                text_dict = page.get_text("dict")
                
                # Process text blocks with layout awareness
                for block in text_dict["blocks"]:
                    if "lines" in block:  # Text block
                        block_text = ""
                        font_info = []
                        
                        for line in block["lines"]:
                            line_text = ""
                            for span in line["spans"]:
                                line_text += span["text"]
                                font_info.append({
                                    "size": span["size"],
                                    "flags": span["flags"],
                                    "font": span["font"]
                                })
                            block_text += line_text + " "
                        
                        if block_text.strip():
                            # Analyze text block
                            block_type = self._classify_text_block_advanced(block_text, font_info)
                            importance = self._calculate_importance_score_advanced(block_text, block_type)
                            entities = self._extract_entities(block_text)
                            keywords = self._extract_keywords(block_text)
                            
                            text_blocks.append(TextBlock(
                                text=block_text.strip(),
                                metadata={
                                    "page_number": page_num + 1,
                                    "font_info": font_info,
                                    "bbox": block["bbox"],
                                    "block_type": block_type
                                },
                                block_type=block_type,
                                page_number=page_num + 1,
                                importance_score=importance,
                                entities=entities,
                                keywords=keywords
                            ))
                
                # Extract images and tables if needed
                images = page.get_images()
                if images:
                    for img_index, img in enumerate(images):
                        # Add image metadata
                        text_blocks.append(TextBlock(
                            text=f"[Image {img_index + 1}]",
                            metadata={
                                "page_number": page_num + 1,
                                "image_index": img_index,
                                "image_info": img
                            },
                            block_type="image",
                            page_number=page_num + 1,
                            importance_score=0.3
                        ))
            
            doc.close()
            
        except Exception as e:
            logger.error("Advanced PDF processing failed, falling back to basic", error=str(e))
            # Fallback to basic PDF processing
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
                        block_type = self._classify_text_block_advanced(para)
                        importance = self._calculate_importance_score_advanced(para, block_type)
                        entities = self._extract_entities(para)
                        keywords = self._extract_keywords(para)
                        
                        text_blocks.append(TextBlock(
                            text=para,
                            metadata={"page_number": page_num + 1},
                            block_type=block_type,
                            page_number=page_num + 1,
                            importance_score=importance,
                            entities=entities,
                            keywords=keywords
                        ))
        
        return text_blocks
    
    async def _process_docx_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced DOCX processing with structure detection"""
        text_blocks = []
        doc = DocxDocument(file_path)
        
        current_section = None
        current_subsection = None
        
        for paragraph in doc.paragraphs:
            if not paragraph.text.strip():
                continue
            
            # Detect document structure
            if paragraph.style.name.startswith('Heading 1'):
                current_section = paragraph.text.strip()
                current_subsection = None
                block_type = 'title'
                importance = 0.9
            elif paragraph.style.name.startswith('Heading 2'):
                current_subsection = paragraph.text.strip()
                block_type = 'subtitle'
                importance = 0.8
            elif paragraph.style.name.startswith('Heading'):
                block_type = 'heading'
                importance = 0.7
            else:
                block_type = 'paragraph'
                importance = self._calculate_importance_score_advanced(paragraph.text, block_type)
            
            entities = self._extract_entities(paragraph.text)
            keywords = self._extract_keywords(paragraph.text)
            
            text_blocks.append(TextBlock(
                text=paragraph.text.strip(),
                metadata={
                    "style": paragraph.style.name,
                    "section": current_section,
                    "subsection": current_subsection
                },
                block_type=block_type,
                section=current_section,
                subsection=current_subsection,
                importance_score=importance,
                entities=entities,
                keywords=keywords
            ))
        
        return text_blocks
    
    async def _process_txt_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced text file processing"""
        text_blocks = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Detect document structure
            sections = self._detect_document_sections(content)
            
            for section in sections:
                block_type = self._classify_text_block_advanced(section['text'])
                importance = self._calculate_importance_score_advanced(section['text'], block_type)
                entities = self._extract_entities(section['text'])
                keywords = self._extract_keywords(section['text'])
                
                text_blocks.append(TextBlock(
                    text=section['text'],
                    metadata={
                        "section_title": section.get('title'),
                        "section_type": section.get('type'),
                        "file_type": "text"
                    },
                    block_type=block_type,
                    section=section.get('title'),
                    importance_score=importance,
                    entities=entities,
                    keywords=keywords
                ))
        
        return text_blocks
    
    async def _process_markdown_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced Markdown processing with structure detection"""
        text_blocks = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Parse markdown structure
            lines = content.split('\n')
            current_section = None
            current_subsection = None
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Detect headers
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.lstrip('# ').strip()
                    
                    if level == 1:
                        current_section = header_text
                        current_subsection = None
                        block_type = 'title'
                        importance = 0.9
                    elif level == 2:
                        current_subsection = header_text
                        block_type = 'subtitle'
                        importance = 0.8
                    else:
                        block_type = 'heading'
                        importance = 0.7
                    
                    entities = self._extract_entities(header_text)
                    keywords = self._extract_keywords(header_text)
                    
                    text_blocks.append(TextBlock(
                        text=header_text,
                        metadata={
                            "level": level,
                            "section": current_section,
                            "subsection": current_subsection
                        },
                        block_type=block_type,
                        section=current_section,
                        subsection=current_subsection,
                        importance_score=importance,
                        entities=entities,
                        keywords=keywords
                    ))
                else:
                    # Regular content
                    block_type = self._classify_text_block_advanced(line)
                    importance = self._calculate_importance_score_advanced(line, block_type)
                    entities = self._extract_entities(line)
                    keywords = self._extract_keywords(line)
                    
                    text_blocks.append(TextBlock(
                        text=line,
                        metadata={
                            "section": current_section,
                            "subsection": current_subsection
                        },
                        block_type=block_type,
                        section=current_section,
                        subsection=current_subsection,
                        importance_score=importance,
                        entities=entities,
                        keywords=keywords
                    ))
        
        return text_blocks
    
    async def _process_csv_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced CSV processing with data analysis"""
        text_blocks = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Add dataset summary
            summary_text = f"Dataset Summary: {len(df)} rows, {len(df.columns)} columns. Columns: {', '.join(df.columns)}"
            text_blocks.append(TextBlock(
                text=summary_text,
                metadata={"data_type": "summary", "row_count": len(df), "column_count": len(df.columns)},
                block_type="summary",
                importance_score=0.8
            ))
            
            # Process each row with context
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                
                if row_text.strip():
                    # Analyze row content
                    entities = self._extract_entities(row_text)
                    keywords = self._extract_keywords(row_text)
                    
                    text_blocks.append(TextBlock(
                        text=row_text,
                        metadata={
                            "row_index": idx,
                            "columns": list(df.columns),
                            "data_type": "tabular"
                        },
                        block_type="table_row",
                        importance_score=0.6,
                        entities=entities,
                        keywords=keywords
                    ))
            
            # Add column analysis
            for col in df.columns:
                col_info = f"Column '{col}': {df[col].dtype}, {df[col].isnull().sum()} null values"
                text_blocks.append(TextBlock(
                    text=col_info,
                    metadata={"column_name": col, "data_type": str(df[col].dtype)},
                    block_type="column_info",
                    importance_score=0.5
                ))
                
        except Exception as e:
            logger.error("CSV processing failed", error=str(e))
            raise
        
        return text_blocks
    
    async def _process_xlsx_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced XLSX processing with multi-sheet support"""
        text_blocks = []
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Sheet summary
                sheet_summary = f"Sheet '{sheet_name}': {len(df)} rows, {len(df.columns)} columns"
                text_blocks.append(TextBlock(
                    text=sheet_summary,
                    metadata={"sheet_name": sheet_name, "row_count": len(df), "column_count": len(df.columns)},
                    block_type="sheet_summary",
                    importance_score=0.7
                ))
                
                # Process rows
                for idx, row in df.iterrows():
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                    
                    if row_text.strip():
                        entities = self._extract_entities(row_text)
                        keywords = self._extract_keywords(row_text)
                        
                        text_blocks.append(TextBlock(
                            text=row_text,
                            metadata={
                                "sheet_name": sheet_name,
                                "row_index": idx,
                                "columns": list(df.columns)
                            },
                            block_type="table_row",
                            importance_score=0.6,
                            entities=entities,
                            keywords=keywords
                        ))
                        
        except Exception as e:
            logger.error("XLSX processing failed", error=str(e))
            raise
        
        return text_blocks
    
    async def _process_json_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced JSON processing with structure analysis"""
        text_blocks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Analyze JSON structure
            structure_info = self._analyze_json_structure(data)
            
            # Add structure summary
            summary_text = f"JSON Structure: {structure_info['type']}, {structure_info['keys']} top-level keys"
            text_blocks.append(TextBlock(
                text=summary_text,
                metadata={"json_structure": structure_info},
                block_type="json_summary",
                importance_score=0.8
            ))
            
            # Process JSON content
            json_text_blocks = self._extract_text_from_json(data)
            text_blocks.extend(json_text_blocks)
            
        except Exception as e:
            logger.error("JSON processing failed", error=str(e))
            raise
        
        return text_blocks
    
    async def _process_html_advanced(self, file_path: str) -> List[TextBlock]:
        """Advanced HTML processing with content extraction"""
        text_blocks = []
        
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract different types of content
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span']):
                text = tag.get_text().strip()
                if text:
                    block_type = self._classify_html_element(tag.name)
                    importance = self._calculate_importance_score_advanced(text, block_type)
                    entities = self._extract_entities(text)
                    keywords = self._extract_keywords(text)
                    
                    text_blocks.append(TextBlock(
                        text=text,
                        metadata={
                            "tag": tag.name,
                            "attributes": dict(tag.attrs),
                            "html_type": "content"
                        },
                        block_type=block_type,
                        importance_score=importance,
                        entities=entities,
                        keywords=keywords
                    ))
                    
        except ImportError:
            logger.warning("BeautifulSoup not available, using basic HTML processing")
            # Basic HTML processing without BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Simple text extraction
            text = re.sub(r'<[^>]+>', '', content)
            text_blocks.append(TextBlock(
                text=text,
                metadata={"html_type": "basic_extraction"},
                block_type="paragraph",
                importance_score=0.5
            ))
        except Exception as e:
            logger.error("HTML processing failed", error=str(e))
            raise
        
        return text_blocks
    
    def _classify_text_block_advanced(self, text: str, font_info: List[Dict] = None) -> str:
        """Advanced text block classification"""
        text_lower = text.lower().strip()
        
        # Check for titles/headings
        if (text.startswith('#') or 
            len(text) < 100 and text.isupper() or
            re.match(r'^[A-Z][^.!?]*$', text) or
            (font_info and any(f.get('size', 0) > 14 for f in font_info))):
            return 'title'
        
        # Check for lists
        if (text.startswith(('•', '-', '*', '1.', '2.', '3.')) or
            re.match(r'^\d+\.\s', text) or
            re.match(r'^[a-zA-Z]\.\s', text)):
            return 'list'
        
        # Check for code
        if ('```' in text or 
            text.startswith('    ') or
            re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*[=\(]', text) or
            'function' in text_lower and '(' in text):
            return 'code'
        
        # Check for tables
        if '|' in text and text.count('|') > 2:
            return 'table'
        
        # Check for questions
        if text.endswith('?') or text_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
            return 'question'
        
        # Check for definitions
        if re.match(r'^[A-Z][a-zA-Z\s]+:\s', text):
            return 'definition'
        
        return 'paragraph'
    
    def _calculate_importance_score_advanced(self, text: str, block_type: str) -> float:
        """Advanced importance score calculation"""
        base_scores = {
            'title': 0.9,
            'subtitle': 0.8,
            'heading': 0.7,
            'summary': 0.8,
            'definition': 0.7,
            'question': 0.6,
            'list': 0.6,
            'table': 0.5,
            'paragraph': 0.5,
            'code': 0.4,
            'image': 0.3
        }
        
        base_score = base_scores.get(block_type, 0.5)
        
        # Adjust based on content characteristics
        text_lower = text.lower()
        
        # Boost for important keywords
        important_keywords = [
            'important', 'critical', 'key', 'main', 'primary', 'essential',
            'summary', 'conclusion', 'overview', 'introduction', 'abstract',
            'warning', 'note', 'tip', 'example', 'best practice'
        ]
        
        keyword_boost = sum(0.05 for keyword in important_keywords if keyword in text_lower)
        
        # Boost for length (more content = more important)
        length_boost = min(0.2, len(text) / 2000)
        
        # Boost for numbers and data
        data_boost = 0.1 if re.search(r'\d+', text) else 0
        
        # Boost for technical terms
        technical_boost = 0.05 if any(term in text_lower for term in ['api', 'function', 'method', 'class', 'algorithm']) else 0
        
        # Boost for entities (if available)
        entity_boost = 0.05 if self._has_entities(text) else 0
        
        final_score = min(1.0, base_score + keyword_boost + length_boost + data_boost + technical_boost + entity_boost)
        
        return round(final_score, 3)
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        if not self.text_processing_available:
            return []
        
        try:
            # Tokenize and tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Extract named entities
            entities = []
            for chunk in ne_chunk(pos_tags):
                if hasattr(chunk, 'label'):
                    entity_text = ' '.join([token for token, pos in chunk.leaves()])
                    entities.append(entity_text)
            
            return entities
        except Exception as e:
            logger.warning("Entity extraction failed", error=str(e))
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        if not self.ml_available:
            return []
        
        try:
            # Use TF-IDF to extract keywords
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top keywords
            scores = tfidf_matrix.toarray()[0]
            top_indices = scores.argsort()[-10:][::-1]  # Top 10 keywords
            
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            return keywords
        except Exception as e:
            logger.warning("Keyword extraction failed", error=str(e))
            return []
    
    def _has_entities(self, text: str) -> bool:
        """Check if text contains entities"""
        entities = self._extract_entities(text)
        return len(entities) > 0
    
    def _detect_document_sections(self, content: str) -> List[Dict[str, Any]]:
        """Detect document sections"""
        sections = []
        
        # Split by common section markers
        section_patterns = [
            r'\n\s*#{1,6}\s+',  # Markdown headers
            r'\n\s*[A-Z][A-Z\s]+\n',  # ALL CAPS headers
            r'\n\s*\d+\.\s+[A-Z]',  # Numbered sections
        ]
        
        current_section = {'text': '', 'title': None, 'type': 'paragraph'}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a section header
            is_header = any(re.match(pattern, f'\n{line}') for pattern in section_patterns)
            
            if is_header:
                # Save current section
                if current_section['text']:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'text': line,
                    'title': line,
                    'type': 'header'
                }
            else:
                # Add to current section
                if current_section['text']:
                    current_section['text'] += '\n' + line
                else:
                    current_section['text'] = line
        
        # Add final section
        if current_section['text']:
            sections.append(current_section)
        
        return sections
    
    def _analyze_json_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze JSON structure"""
        if isinstance(data, dict):
            return {
                'type': 'object',
                'keys': list(data.keys()),
                'size': len(data)
            }
        elif isinstance(data, list):
            return {
                'type': 'array',
                'length': len(data),
                'item_types': list(set(type(item).__name__ for item in data[:10]))
            }
        else:
            return {
                'type': type(data).__name__,
                'value': str(data)[:100]
            }
    
    def _extract_text_from_json(self, data: Any, path: str = "") -> List[TextBlock]:
        """Extract text content from JSON"""
        text_blocks = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                text_blocks.extend(self._extract_text_from_json(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                text_blocks.extend(self._extract_text_from_json(item, current_path))
        elif isinstance(data, str) and len(data) > 10:
            # Extract meaningful text
            block_type = self._classify_text_block_advanced(data)
            importance = self._calculate_importance_score_advanced(data, block_type)
            entities = self._extract_entities(data)
            keywords = self._extract_keywords(data)
            
            text_blocks.append(TextBlock(
                text=data,
                metadata={"json_path": path},
                block_type=block_type,
                importance_score=importance,
                entities=entities,
                keywords=keywords
            ))
        
        return text_blocks
    
    def _classify_html_element(self, tag_name: str) -> str:
        """Classify HTML element type"""
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        if tag_name in heading_tags:
            return 'title'
        elif tag_name == 'p':
            return 'paragraph'
        elif tag_name in ['ul', 'ol', 'li']:
            return 'list'
        elif tag_name in ['code', 'pre']:
            return 'code'
        else:
            return 'paragraph'
    
    def create_semantic_chunks(self, text_blocks: List[TextBlock]) -> List[Chunk]:
        """Create semantic chunks from text blocks"""
        if self.chunking_strategy == ChunkingStrategy.SEMANTIC:
            return self._create_semantic_chunks(text_blocks)
        elif self.chunking_strategy == ChunkingStrategy.HIERARCHICAL:
            return self._create_hierarchical_chunks(text_blocks)
        elif self.chunking_strategy == ChunkingStrategy.ADAPTIVE:
            return self._create_adaptive_chunks(text_blocks)
        else:
            return self._create_basic_chunks(text_blocks)
    
    def _create_semantic_chunks(self, text_blocks: List[TextBlock]) -> List[Chunk]:
        """Create semantic chunks based on content meaning"""
        chunks = []
        current_chunk_blocks = []
        current_size = 0
        
        for block in text_blocks:
            block_size = len(block.text)
            
            # Check if adding this block would exceed size limit
            if current_size + block_size > self.chunk_size and current_chunk_blocks:
                # Create chunk from current blocks
                chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_blocks = self._get_overlap_blocks(current_chunk_blocks)
                current_chunk_blocks = overlap_blocks + [block]
                current_size = sum(len(b.text) for b in current_chunk_blocks)
            else:
                current_chunk_blocks.append(block)
                current_size += block_size
        
        # Add final chunk
        if current_chunk_blocks:
            chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
            chunks.append(chunk)
        
        return chunks
    
    def _create_hierarchical_chunks(self, text_blocks: List[TextBlock]) -> List[Chunk]:
        """Create hierarchical chunks based on document structure"""
        chunks = []
        current_section = None
        current_chunk_blocks = []
        
        for block in text_blocks:
            # Check if this is a new section
            if block.section and block.section != current_section:
                # Save current section chunk
                if current_chunk_blocks:
                    chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
                    chunks.append(chunk)
                
                # Start new section
                current_section = block.section
                current_chunk_blocks = [block]
            else:
                current_chunk_blocks.append(block)
                
                # Check if chunk is getting too large
                if sum(len(b.text) for b in current_chunk_blocks) > self.chunk_size:
                    chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
                    chunks.append(chunk)
                    current_chunk_blocks = []
        
        # Add final chunk
        if current_chunk_blocks:
            chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
            chunks.append(chunk)
        
        return chunks
    
    def _create_adaptive_chunks(self, text_blocks: List[TextBlock]) -> List[Chunk]:
        """Create adaptive chunks based on content type and importance"""
        chunks = []
        current_chunk_blocks = []
        current_size = 0
        
        for block in text_blocks:
            # Adjust chunk size based on content type
            adaptive_size = self._get_adaptive_chunk_size(block)
            
            if current_size + len(block.text) > adaptive_size and current_chunk_blocks:
                chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_blocks = [block]
                current_size = len(block.text)
            else:
                current_chunk_blocks.append(block)
                current_size += len(block.text)
        
        # Add final chunk
        if current_chunk_blocks:
            chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
            chunks.append(chunk)
        
        return chunks
    
    def _create_basic_chunks(self, text_blocks: List[TextBlock]) -> List[Chunk]:
        """Create basic fixed-size chunks"""
        chunks = []
        current_chunk_blocks = []
        current_size = 0
        
        for block in text_blocks:
            if current_size + len(block.text) > self.chunk_size and current_chunk_blocks:
                chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_blocks = self._get_overlap_blocks(current_chunk_blocks)
                current_chunk_blocks = overlap_blocks + [block]
                current_size = sum(len(b.text) for b in current_chunk_blocks)
            else:
                current_chunk_blocks.append(block)
                current_size += len(block.text)
        
        # Add final chunk
        if current_chunk_blocks:
            chunk = self._create_chunk_from_blocks(current_chunk_blocks, len(chunks))
            chunks.append(chunk)
        
        return chunks
    
    def _get_adaptive_chunk_size(self, block: TextBlock) -> int:
        """Get adaptive chunk size based on block characteristics"""
        base_size = self.chunk_size
        
        # Adjust based on block type
        if block.block_type == 'title':
            return min(base_size, 500)  # Smaller chunks for titles
        elif block.block_type == 'code':
            return min(base_size, 2000)  # Larger chunks for code
        elif block.block_type == 'table':
            return min(base_size, 1500)  # Medium chunks for tables
        elif block.importance_score > 0.8:
            return min(base_size, 800)  # Smaller chunks for important content
        
        return base_size
    
    def _create_chunk_from_blocks(self, blocks: List[TextBlock], chunk_index: int) -> Chunk:
        """Create a chunk from text blocks"""
        chunk_text = " ".join(block.text for block in blocks)
        chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
        
        # Calculate chunk metadata
        metadata = {
            "chunk_type": self.chunking_strategy.value,
            "block_count": len(blocks),
            "total_length": len(chunk_text),
            "avg_importance": sum(block.importance_score for block in blocks) / len(blocks),
            "block_types": [block.block_type for block in blocks],
            "sections": list(set(block.section for block in blocks if block.section)),
            "subsections": list(set(block.subsection for block in blocks if block.subsection)),
            "page_numbers": list(set(block.page_number for block in blocks if block.page_number)),
            "entities": list(set(entity for block in blocks for entity in block.entities)),
            "keywords": list(set(keyword for block in blocks for keyword in block.keywords))
        }
        
        # Add metadata from blocks
        for block in blocks:
            metadata.update(block.metadata)
        
        return Chunk(
            text=chunk_text,
            chunk_id=chunk_id,
            document_id=0,  # Will be set when saving to database
            workspace_id="",  # Will be set when saving to database
            chunk_index=chunk_index,
            metadata=metadata,
            importance_score=metadata["avg_importance"],
            entities=metadata["entities"],
            keywords=metadata["keywords"]
        )
    
    def _get_overlap_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """Get blocks for overlap in next chunk"""
        if len(blocks) <= 1:
            return []
        
        # Take last 1-2 blocks for overlap
        overlap_count = min(2, len(blocks))
        return blocks[-overlap_count:]


# Global instance
production_file_processor = ProductionFileProcessor(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy=ChunkingStrategy.SEMANTIC
)
