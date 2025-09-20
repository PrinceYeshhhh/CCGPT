"""
File parsing utilities for extracting text from various file formats
"""

import os
import re
from typing import List, Tuple, Dict, Any
import PyPDF2
import pandas as pd
from docx import Document as DocxDocument
import structlog

logger = structlog.get_logger()


def extract_text_from_file(file_path: str, content_type: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extract text blocks from file with metadata
    
    Args:
        file_path: Path to the file
        content_type: MIME type of the file
        
    Returns:
        List of (text_block, metadata) tuples
    """
    try:
        if content_type == "application/pdf":
            return _extract_pdf_text(file_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return _extract_docx_text(file_path)
        elif content_type == "text/csv":
            return _extract_csv_text(file_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return _extract_xlsx_text(file_path)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    except Exception as e:
        logger.error(
            "Text extraction failed",
            error=str(e),
            file_path=file_path,
            content_type=content_type
        )
        raise


def _extract_pdf_text(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract text from PDF file with page metadata"""
    text_blocks = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        # Clean the text
                        cleaned_text = _clean_text(page_text)
                        if cleaned_text:
                            metadata = {
                                "page": page_num + 1,
                                "char_range": [0, len(cleaned_text)],
                                "source": "pdf"
                            }
                            text_blocks.append((cleaned_text, metadata))
                except Exception as e:
                    logger.warning(
                        "Failed to extract text from PDF page",
                        error=str(e),
                        page_num=page_num,
                        file_path=file_path
                    )
                    continue
                    
    except Exception as e:
        logger.error("PDF text extraction failed", error=str(e), file_path=file_path)
        raise
    
    return text_blocks


def _extract_docx_text(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract text from DOCX file with paragraph metadata"""
    text_blocks = []
    
    try:
        doc = DocxDocument(file_path)
        
        for para_num, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if text:
                # Clean the text
                cleaned_text = _clean_text(text)
                if cleaned_text:
                    metadata = {
                        "paragraph": para_num + 1,
                        "char_range": [0, len(cleaned_text)],
                        "source": "docx"
                    }
                    text_blocks.append((cleaned_text, metadata))
                    
    except Exception as e:
        logger.error("DOCX text extraction failed", error=str(e), file_path=file_path)
        raise
    
    return text_blocks


def _extract_csv_text(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract text from CSV file with row metadata"""
    text_blocks = []
    
    try:
        df = pd.read_csv(file_path)
        
        # Extract headers as context
        headers = list(df.columns)
        if headers:
            header_text = " | ".join(str(h) for h in headers)
            metadata = {
                "row": 0,
                "char_range": [0, len(header_text)],
                "source": "csv_headers"
            }
            text_blocks.append((header_text, metadata))
        
        # Extract data rows
        for index, row in df.iterrows():
            row_text = " | ".join(str(cell) if pd.notna(cell) else "" for cell in row)
            if row_text.strip():
                cleaned_text = _clean_text(row_text)
                if cleaned_text:
                    metadata = {
                        "row": index + 1,
                        "char_range": [0, len(cleaned_text)],
                        "source": "csv_data"
                    }
                    text_blocks.append((cleaned_text, metadata))
                    
    except Exception as e:
        logger.error("CSV text extraction failed", error=str(e), file_path=file_path)
        raise
    
    return text_blocks


def _extract_xlsx_text(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract text from XLSX file with sheet and cell metadata"""
    text_blocks = []
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Extract sheet name as context
            sheet_text = f"Sheet: {sheet_name}"
            metadata = {
                "sheet": sheet_name,
                "row": 0,
                "char_range": [0, len(sheet_text)],
                "source": "xlsx_sheet"
            }
            text_blocks.append((sheet_text, metadata))
            
            # Extract headers
            headers = list(df.columns)
            if headers:
                header_text = " | ".join(str(h) for h in headers)
                metadata = {
                    "sheet": sheet_name,
                    "row": 0,
                    "char_range": [0, len(header_text)],
                    "source": "xlsx_headers"
                }
                text_blocks.append((header_text, metadata))
            
            # Extract data rows
            for index, row in df.iterrows():
                row_text = " | ".join(str(cell) if pd.notna(cell) else "" for cell in row)
                if row_text.strip():
                    cleaned_text = _clean_text(row_text)
                    if cleaned_text:
                        metadata = {
                            "sheet": sheet_name,
                            "row": index + 1,
                            "char_range": [0, len(cleaned_text)],
                            "source": "xlsx_data"
                        }
                        text_blocks.append((cleaned_text, metadata))
                        
    except Exception as e:
        logger.error("XLSX text extraction failed", error=str(e), file_path=file_path)
        raise
    
    return text_blocks


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
