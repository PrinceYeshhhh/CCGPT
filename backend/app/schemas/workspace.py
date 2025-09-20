from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class WorkspaceSettings(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    timezone: str = "UTC"
    created_at: str
    updated_at: str

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    support_email: Optional[EmailStr] = None
    timezone: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: str

class LogoUploadResponse(BaseModel):
    logo_url: str
    message: str

class LogoDeleteResponse(BaseModel):
    message: str
