"""
Settings endpoints for user and organization management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid
import secrets
import pyotp
import qrcode
import io
import base64

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.models.team_member import TeamMember as TeamMemberModel
from app.schemas.settings import (
    ProfileUpdate, PasswordChange, OrganizationUpdate, TeamMemberInvite,
    TeamMember, NotificationSettings, AppearanceSettings, TwoFactorSetup,
    SettingsResponse, FileUploadResponse
)
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.workspace import WorkspaceService
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user settings"""
    try:
        # Get workspace
        workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Get team members
        team_members = db.query(TeamMemberModel).filter(
            TeamMemberModel.workspace_id == current_user.workspace_id
        ).all()

        team_members_data = [
            TeamMember(
                id=member.id,
                email=member.email,
                full_name=member.full_name,
                role=member.role,
                status=member.status,
                joined_at=member.created_at,
                last_active=member.last_active
            )
            for member in team_members
        ]

        return SettingsResponse(
            profile=ProfileUpdate(
                username=current_user.username or current_user.email.split('@')[0],
                email=current_user.email,
                full_name=current_user.full_name,
                business_name=current_user.business_name,
                business_domain=current_user.business_domain,
                profile_picture_url=current_user.profile_picture_url
            ),
            organization=OrganizationUpdate(
                name=workspace.name,
                description=workspace.description,
                website_url=workspace.website_url,
                support_email=workspace.support_email,
                logo_url=workspace.logo_url,
                custom_domain=workspace.custom_domain,
                widget_domain=workspace.widget_domain,
                timezone=workspace.timezone or "UTC"
            ),
            notifications=NotificationSettings(
                email_notifications=getattr(current_user, 'email_notifications', True),
                browser_notifications=getattr(current_user, 'browser_notifications', False),
                usage_alerts=getattr(current_user, 'usage_alerts', True),
                billing_updates=getattr(current_user, 'billing_updates', True),
                security_alerts=getattr(current_user, 'security_alerts', True),
                product_updates=getattr(current_user, 'product_updates', False)
            ),
            appearance=AppearanceSettings(
                theme=getattr(current_user, 'theme', 'system'),
                layout=getattr(current_user, 'layout', 'comfortable'),
                language=getattr(current_user, 'language', 'en'),
                timezone=getattr(current_user, 'timezone', 'UTC')
            ),
            two_factor_enabled=getattr(current_user, 'two_factor_enabled', False),
            team_members=team_members_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch settings"
        )


@router.put("/profile", response_model=ProfileUpdate)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        # Check if username is already taken by another user
        if profile_data.username != current_user.username:
            existing_user = db.query(User).filter(
                User.username == profile_data.username,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        # Check if email is already taken by another user
        if profile_data.email != current_user.email:
            existing_user = db.query(User).filter(
                User.email == profile_data.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )

        # Update user profile
        current_user.username = profile_data.username
        current_user.email = profile_data.email
        current_user.full_name = profile_data.full_name
        current_user.business_name = profile_data.business_name
        current_user.business_domain = profile_data.business_domain
        current_user.profile_picture_url = profile_data.profile_picture_url
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return profile_data

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return {"message": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )


@router.put("/organization", response_model=OrganizationUpdate)
async def update_organization(
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update organization settings"""
    try:
        # Get workspace
        workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Update workspace
        workspace.name = org_data.name
        workspace.description = org_data.description
        workspace.website_url = org_data.website_url
        workspace.support_email = org_data.support_email
        workspace.logo_url = org_data.logo_url
        workspace.custom_domain = org_data.custom_domain
        workspace.widget_domain = org_data.widget_domain
        workspace.timezone = org_data.timezone
        workspace.updated_at = datetime.utcnow()

        db.commit()

        return org_data

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.post("/team/invite")
async def invite_team_member(
    invite_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a team member to the workspace"""
    try:
        # Check if user is already a member
        existing_member = db.query(TeamMemberModel).filter(
            TeamMemberModel.workspace_id == current_user.workspace_id,
            TeamMemberModel.email == invite_data.email
        ).first()

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this workspace"
            )

        # Create team member invitation
        invitation_token = secrets.token_urlsafe(32)
        team_member = TeamMemberModel(
            workspace_id=current_user.workspace_id,
            email=invite_data.email,
            role=invite_data.role,
            status="pending",
            invitation_token=invitation_token,
            invited_by=current_user.id
        )

        db.add(team_member)
        db.commit()

        # TODO: Send invitation email

        return {
            "message": "Invitation sent successfully",
            "invitation_token": invitation_token
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation"
        )


@router.get("/team", response_model=List[TeamMember])
async def get_team_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team members for the workspace"""
    try:
        team_members = db.query(TeamMemberModel).filter(
            TeamMemberModel.workspace_id == current_user.workspace_id
        ).all()

        return [
            TeamMember(
                id=member.id,
                email=member.email,
                full_name=member.full_name,
                role=member.role,
                status=member.status,
                joined_at=member.created_at,
                last_active=member.last_active
            )
            for member in team_members
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team members"
        )


@router.put("/notifications", response_model=NotificationSettings)
async def update_notifications(
    notification_data: NotificationSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    try:
        # Update user notification preferences
        current_user.email_notifications = notification_data.email_notifications
        current_user.browser_notifications = notification_data.browser_notifications
        current_user.usage_alerts = notification_data.usage_alerts
        current_user.billing_updates = notification_data.billing_updates
        current_user.security_alerts = notification_data.security_alerts
        current_user.product_updates = notification_data.product_updates
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return notification_data

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications"
        )


@router.put("/appearance", response_model=AppearanceSettings)
async def update_appearance(
    appearance_data: AppearanceSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appearance preferences"""
    try:
        # Update user appearance preferences
        current_user.theme = appearance_data.theme
        current_user.layout = appearance_data.layout
        current_user.language = appearance_data.language
        current_user.timezone = appearance_data.timezone
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return appearance_data

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appearance"
        )


@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup two-factor authentication"""
    try:
        # Generate secret
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp.provisioning_uri(
            name=current_user.email,
            issuer_name="CustomerCareGPT"
        ))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Store secret temporarily (not enabled yet)
        current_user.two_factor_secret = secret
        current_user.two_factor_backup_codes = backup_codes
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return TwoFactorSetup(
            secret=secret,
            qr_code=f"data:image/png;base64,{qr_code}",
            backup_codes=backup_codes
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )


@router.post("/2fa/verify")
async def verify_two_factor(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and enable two-factor authentication"""
    try:
        if not current_user.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up"
            )

        # Verify code
        totp = pyotp.TOTP(current_user.two_factor_secret)
        if not totp.verify(code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # Enable 2FA
        current_user.two_factor_enabled = True
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return {"message": "Two-factor authentication enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )


@router.post("/upload/profile-picture", response_model=FileUploadResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Validate file size (2MB max)
        if file.size and file.size > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 2MB"
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"profile_{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        
        # In production, upload to cloud storage (AWS S3, etc.)
        # For now, save to local storage
        upload_dir = "uploads/profile_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update user profile picture URL
        profile_url = f"/uploads/profile_pictures/{filename}"
        current_user.profile_picture_url = profile_url
        current_user.updated_at = datetime.utcnow()

        db.commit()

        return FileUploadResponse(
            url=profile_url,
            filename=filename,
            size=len(content),
            content_type=file.content_type
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )


@router.post("/upload/organization-logo", response_model=FileUploadResponse)
async def upload_organization_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload organization logo"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Validate file size (5MB max)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )

        # Get workspace
        workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        filename = f"logo_{workspace.id}_{uuid.uuid4().hex}.{file_extension}"
        
        # In production, upload to cloud storage
        upload_dir = "uploads/organization_logos"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update workspace logo URL
        logo_url = f"/uploads/organization_logos/{filename}"
        workspace.logo_url = logo_url
        workspace.updated_at = datetime.utcnow()

        db.commit()

        return FileUploadResponse(
            url=logo_url,
            filename=filename,
            size=len(content),
            content_type=file.content_type
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload organization logo"
        )
