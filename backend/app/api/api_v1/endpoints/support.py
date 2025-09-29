"""
Support endpoints for contact support and demo scheduling
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import structlog

from app.services.email_service import EmailService

logger = structlog.get_logger()
router = APIRouter()


class ContactSupportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    organization: Optional[str] = Field(None, max_length=100, description="Organization name")
    email: EmailStr = Field(..., description="Email address")
    question: str = Field(..., min_length=10, max_length=2000, description="Question or issue")


class ScheduleDemoRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    organization: Optional[str] = Field(None, max_length=100, description="Organization name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    preferredDate: str = Field(..., description="Preferred date for demo")
    preferredTime: str = Field(..., description="Preferred time for demo")
    timezone: str = Field(default="UTC", description="Timezone")
    companySize: Optional[str] = Field(None, description="Company size")
    useCase: Optional[str] = Field(None, description="Primary use case")
    additionalNotes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SupportResponse(BaseModel):
    success: bool
    message: str


@router.post("/contact", response_model=SupportResponse)
async def contact_support(request: ContactSupportRequest):
    """Submit a contact support request"""
    try:
        email_service = EmailService()
        
        # Send email to admin
        admin_email_sent = email_service.send_contact_support_email(request.dict())
        
        # Send confirmation email to user
        user_email_sent = email_service.send_confirmation_email(
            email=request.email,
            email_type='contact_support',
            data=request.dict()
        )
        
        if admin_email_sent and user_email_sent:
            logger.info(f"Contact support request submitted by {request.email}")
            return SupportResponse(
                success=True,
                message="Your message has been sent successfully. We'll get back to you soon!"
            )
        else:
            logger.error(f"Failed to send contact support emails for {request.email}")
            return SupportResponse(
                success=False,
                message="Failed to send your message. Please try again later."
            )
            
    except Exception as e:
        logger.error(f"Error processing contact support request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your request. Please try again later."
        )


@router.post("/schedule-demo", response_model=SupportResponse)
async def schedule_demo(request: ScheduleDemoRequest):
    """Schedule a demo request"""
    try:
        email_service = EmailService()
        
        # Send email to admin
        admin_email_sent = email_service.send_demo_request_email(request.dict())
        
        # Send confirmation email to user
        user_email_sent = email_service.send_confirmation_email(
            email=request.email,
            email_type='demo_request',
            data=request.dict()
        )
        
        if admin_email_sent and user_email_sent:
            logger.info(f"Demo request submitted by {request.email}")
            return SupportResponse(
                success=True,
                message="Your demo request has been submitted successfully. We'll contact you soon to confirm the details!"
            )
        else:
            logger.error(f"Failed to send demo request emails for {request.email}")
            return SupportResponse(
                success=False,
                message="Failed to submit your demo request. Please try again later."
            )
            
    except Exception as e:
        logger.error(f"Error processing demo request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your request. Please try again later."
        )


@router.get("/test-email")
async def test_email_configuration():
    """Test email configuration (admin only)"""
    try:
        email_service = EmailService()
        
        # This would typically require admin authentication
        # For now, we'll just test the configuration
        test_email = "test@example.com"
        success = email_service.send_test_email(test_email)
        
        if success:
            return {"success": True, "message": "Email configuration is working correctly"}
        else:
            return {"success": False, "message": "Email configuration has issues"}
            
    except Exception as e:
        logger.error(f"Error testing email configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test email configuration"
        )
