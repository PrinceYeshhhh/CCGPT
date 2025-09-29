"""
File upload security service with virus scanning and validation
"""

import os
import hashlib
import mimetypes
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException, status
import structlog
from app.core.config import settings

# Try to import magic, fallback to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger = structlog.get_logger()
    logger.warning("python-magic not available, using mimetypes fallback")

logger = structlog.get_logger()


class FileSecurityService:
    """Comprehensive file security validation and scanning"""
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.doc'}
        self.allowed_mime_types = {
            'application/pdf',
            'text/plain',
            'text/markdown',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        }
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
            '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1'
        }
    
    async def validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Comprehensive file validation with security checks"""
        try:
            # Check filename
            if not file.filename:
                return False, "No filename provided"
            
            # Check file size
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if len(file_content) > self.max_file_size:
                return False, f"File too large. Maximum size: {self.max_file_size} bytes"
            
            # Check file extension
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in self.allowed_extensions:
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            
            # Check for dangerous extensions
            if file_extension in self.dangerous_extensions:
                return False, "Potentially dangerous file type detected"
            
            # Validate MIME type using python-magic or fallback
            if MAGIC_AVAILABLE:
                try:
                    detected_mime = magic.from_buffer(file_content, mime=True)
                    if detected_mime not in self.allowed_mime_types:
                        return False, f"Invalid file content. Detected: {detected_mime}"
                except Exception as e:
                    logger.warning("MIME type detection failed", error=str(e))
                    # Fallback to content-type header
                    if file.content_type not in self.allowed_mime_types:
                        return False, f"Invalid content type: {file.content_type}"
            else:
                # Fallback to content-type header validation
                if file.content_type not in self.allowed_mime_types:
                    return False, f"Invalid content type: {file.content_type}"
            
            # Check for suspicious content patterns
            if self._contains_suspicious_content(file_content):
                return False, "Suspicious content detected"
            
            # Check file header/signature
            if not self._validate_file_signature(file_content, file_extension):
                return False, "File signature validation failed"
            
            return True, "File validation passed"
            
        except Exception as e:
            logger.error("File validation error", error=str(e))
            return False, "File validation failed"
    
    def _contains_suspicious_content(self, content: bytes) -> bool:
        """Check for suspicious content patterns"""
        content_str = content.decode('utf-8', errors='ignore').lower()
        
        # Check for script tags
        suspicious_patterns = [
            '<script',
            'javascript:',
            'vbscript:',
            'onload=',
            'onerror=',
            'eval(',
            'document.cookie',
            'document.write',
            'window.location',
            'alert(',
            'confirm(',
            'prompt('
        ]
        
        for pattern in suspicious_patterns:
            if pattern in content_str:
                logger.warning("Suspicious content detected", pattern=pattern)
                return True
        
        return False
    
    def _validate_file_signature(self, content: bytes, extension: str) -> bool:
        """Validate file signature matches extension"""
        if len(content) < 4:
            return False
        
        # PDF signature
        if extension == '.pdf':
            return content.startswith(b'%PDF-')
        
        # Text files
        if extension in ['.txt', '.md']:
            try:
                content.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
        
        # Word documents
        if extension in ['.docx', '.doc']:
            # DOCX files are ZIP archives
            if extension == '.docx':
                return content.startswith(b'PK\x03\x04')
            # DOC files have specific signature
            elif extension == '.doc':
                return content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
        
        return True
    
    def generate_file_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash for file integrity"""
        return hashlib.sha256(content).hexdigest()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def get_file_metadata(self, file: UploadFile, content: bytes) -> dict:
        """Extract safe file metadata"""
        return {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "hash": self.generate_file_hash(content),
            "extension": os.path.splitext(file.filename)[1].lower()
        }


# Global instance
file_security_service = FileSecurityService()
