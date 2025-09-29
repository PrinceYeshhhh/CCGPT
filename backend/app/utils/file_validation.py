"""
Standardized file validation utilities
"""

from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
import structlog

# Try to import magic, fallback to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    import mimetypes

logger = structlog.get_logger()

class FileValidator:
    """Standardized file validation across the application"""
    
    # Allowed file types and their MIME types
    ALLOWED_TYPES = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'txt': ['text/plain'],
        'md': ['text/markdown', 'text/x-markdown'],
        'html': ['text/html'],
        'csv': ['text/csv'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'json': ['application/json'],
        'rtf': ['application/rtf'],
        'odt': ['application/vnd.oasis.opendocument.text'],
        'pages': ['application/vnd.apple.pages'],
        'epub': ['application/epub+zip']
    }
    
    # Maximum file sizes by plan (in bytes)
    MAX_FILE_SIZES = {
        'free': 5 * 1024 * 1024,  # 5MB
        'free_trial': 10 * 1024 * 1024,  # 10MB
        'starter': 25 * 1024 * 1024,  # 25MB
        'pro': 50 * 1024 * 1024,  # 50MB
        'enterprise': 100 * 1024 * 1024,  # 100MB
        'white_label': 200 * 1024 * 1024  # 200MB
    }
    
    # Dangerous file extensions to block
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.iso', '.zip', '.rar', '.7z', '.tar',
        '.gz', '.bz2', '.xz', '.php', '.asp', '.jsp', '.py', '.rb', '.pl',
        '.sh', '.ps1', '.psm1', '.psd1', '.ps1xml', '.psc1', '.pssc'
    }
    
    @classmethod
    def validate_file(
        self,
        file: UploadFile,
        plan_tier: str = 'free',
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate a file upload
        
        Args:
            file: The uploaded file
            plan_tier: User's plan tier for size limits
            max_size: Override max size limit
            
        Returns:
            Dict with validation results
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Check file name
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name is required"
                )
            
            # Check for dangerous extensions
            file_extension = self._get_file_extension(file.filename)
            if file_extension in self.DANGEROUS_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type '{file_extension}' is not allowed for security reasons"
                )
            
            # Check file size
            max_allowed_size = max_size or self.MAX_FILE_SIZES.get(plan_tier, self.MAX_FILE_SIZES['free'])
            if file.size and file.size > max_allowed_size:
                size_mb = max_allowed_size / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds the limit for your {plan_tier} plan ({size_mb:.1f}MB max)"
                )
            
            # Detect actual file type
            file_content = file.file.read(1024)  # Read first 1KB for magic detection
            file.file.seek(0)  # Reset file pointer
            
            if MAGIC_AVAILABLE:
                detected_mime = magic.from_buffer(file_content, mime=True)
            else:
                # Fallback to mimetypes
                detected_mime = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            declared_mime = file.content_type or 'application/octet-stream'
            
            # Validate file type
            is_valid_type = self._is_valid_file_type(file_extension, detected_mime, declared_mime)
            
            if not is_valid_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not supported. Allowed types: {', '.join(self.ALLOWED_TYPES.keys())}"
                )
            
            return {
                "valid": True,
                "file_type": file_extension,
                "mime_type": detected_mime,
                "size": file.size,
                "filename": file.filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File validation failed"
            )
    
    @classmethod
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' not in filename:
            return ''
        return '.' + filename.split('.')[-1].lower()
    
    @classmethod
    def _is_valid_file_type(
        self,
        file_extension: str,
        detected_mime: str,
        declared_mime: str
    ) -> bool:
        """Check if file type is valid"""
        ext = file_extension.lstrip('.').lower()
        
        # Check if extension is in allowed types
        if ext not in self.ALLOWED_TYPES:
            return False
        
        # Check if MIME type matches
        allowed_mimes = self.ALLOWED_TYPES[ext]
        return detected_mime in allowed_mimes or declared_mime in allowed_mimes
    
    @classmethod
    def get_allowed_types(self) -> List[str]:
        """Get list of allowed file extensions"""
        return list(self.ALLOWED_TYPES.keys())
    
    @classmethod
    def get_max_size_for_plan(self, plan_tier: str) -> int:
        """Get maximum file size for a plan tier"""
        return self.MAX_FILE_SIZES.get(plan_tier, self.MAX_FILE_SIZES['free'])
    
    @classmethod
    def is_dangerous_file(self, filename: str) -> bool:
        """Check if file is potentially dangerous"""
        file_extension = self._get_file_extension(filename)
        return file_extension in self.DANGEROUS_EXTENSIONS
