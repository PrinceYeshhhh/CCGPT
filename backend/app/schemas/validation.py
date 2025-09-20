"""
Input validation schemas for security and data integrity
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
import re
from datetime import datetime

class SanitizedString(str):
    """String type that automatically sanitizes input"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', v)
        sanitized = re.sub(r'[^\w\s\-_.,!?@#$%^&*()+=\[\]{}|\\:;]', '', sanitized)
        
        return cls(sanitized)

class EmailValidation(BaseModel):
    """Email validation with security checks"""
    email: str = Field(..., min_length=5, max_length=255)
    
    @validator('email')
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email is required')
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Email contains suspicious content')
        
        return v.lower().strip()

class PasswordValidation(BaseModel):
    """Password validation with security requirements"""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password is required')
        
        # Check minimum length
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', 'dragon'
        ]
        
        if v.lower() in weak_passwords:
            raise ValueError('Password is too common')
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', v):
            raise ValueError('Password cannot contain more than 2 consecutive identical characters')
        
        return v

class QueryValidation(BaseModel):
    """Query validation for RAG endpoints"""
    query: SanitizedString = Field(..., min_length=1, max_length=1000)
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<[^>]*>',
            r'SELECT\s+.*FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET',
            r'DELETE\s+FROM',
            r'DROP\s+TABLE',
            r'UNION\s+SELECT',
            r'OR\s+1=1',
            r'AND\s+1=1'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Query contains suspicious content')
        
        return v.strip()

class FileUploadValidation(BaseModel):
    """File upload validation"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=10485760)  # Max 10MB
    file_type: str = Field(..., min_length=1, max_length=100)
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v:
            raise ValueError('Filename is required')
        
        # Check for suspicious characters
        if re.search(r'[<>:"/\\|?*]', v):
            raise ValueError('Filename contains invalid characters')
        
        # Check for path traversal attempts
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError('Filename contains path traversal characters')
        
        return v
    
    @validator('file_type')
    def validate_file_type(cls, v):
        allowed_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        
        if v not in allowed_types:
            raise ValueError(f'File type {v} is not allowed')
        
        return v

class WorkspaceValidation(BaseModel):
    """Workspace validation"""
    name: SanitizedString = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Workspace name is required')
        
        # Check for suspicious patterns
        if re.search(r'<[^>]*>', v):
            raise ValueError('Workspace name contains HTML tags')
        
        return v.strip()
    
    @validator('domain')
    def validate_domain(cls, v):
        if v is None:
            return v
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, v):
            raise ValueError('Invalid domain format')
        
        return v.lower().strip()

class ChatMessageValidation(BaseModel):
    """Chat message validation"""
    content: SanitizedString = Field(..., min_length=1, max_length=5000)
    role: str = Field(..., regex='^(user|assistant)$')
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contains suspicious content')
        
        return v.strip()

class EmbedConfigValidation(BaseModel):
    """Embed configuration validation"""
    theme: Optional[Dict[str, Any]] = None
    welcome_message: Optional[SanitizedString] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    @validator('welcome_message')
    def validate_welcome_message(cls, v):
        if v is None:
            return v
        
        # Check for suspicious patterns
        if re.search(r'<[^>]*>', v):
            raise ValueError('Welcome message contains HTML tags')
        
        return v.strip()
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        if v is None:
            return v
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid avatar URL format')
        
        return v.strip()

class BillingValidation(BaseModel):
    """Billing validation"""
    plan_tier: str = Field(..., regex='^(starter|pro|enterprise|white_label)$')
    success_url: Optional[str] = Field(None, max_length=500)
    cancel_url: Optional[str] = Field(None, max_length=500)
    
    @validator('success_url', 'cancel_url')
    def validate_url(cls, v):
        if v is None:
            return v
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid URL format')
        
        return v.strip()

class PaginationValidation(BaseModel):
    """Pagination validation"""
    page: int = Field(1, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be greater than 0')
        return v
    
    @validator('page_size')
    def validate_page_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v

class SearchValidation(BaseModel):
    """Search validation"""
    query: SanitizedString = Field(..., min_length=1, max_length=500)
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[str] = Field(None, regex='^(asc|desc)$')
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<[^>]*>'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Search query contains suspicious content')
        
        return v.strip()
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v is None:
            return v
        
        # Check for suspicious characters
        if re.search(r'[^a-zA-Z0-9_]', v):
            raise ValueError('Sort field contains invalid characters')
        
        return v
