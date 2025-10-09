"""
Integration tests for settings and user management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime
import io
import base64

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.team_member import TeamMember
from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_workspace(db_session):
    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        description="Test workspace for settings",
        website_url="https://test.com",
        support_email="support@test.com",
        timezone="UTC"
    )
    db_session.add(workspace)
    db_session.commit()
    return workspace


@pytest.fixture
def test_user(db_session, test_workspace):
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        business_name="Test Business",
        business_domain="test.com",
        hashed_password="hashed_password",
        workspace_id=test_workspace.id,
        email_notifications=True,
        browser_notifications=False,
        usage_alerts=True,
        billing_updates=True,
        security_alerts=True,
        product_updates=False,
        theme="system",
        layout="comfortable",
        language="en",
        timezone="UTC"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_token(test_user):
    from app.services.auth import AuthService
    auth_service = AuthService()
    return auth_service.create_access_token({"sub": test_user.email})


def test_get_settings_success(client, db_session, test_user, test_workspace, auth_token):
    """Test getting user settings successfully"""
    # Add team members
    team_member = TeamMember(
        workspace_id=test_workspace.id,
        email="member@example.com",
        full_name="Team Member",
        role="admin",
        status="active",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db_session.add(team_member)
    db_session.commit()
    
    response = client.get(
        "/api/v1/settings/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check profile data
    assert data["profile"]["username"] == "testuser"
    assert data["profile"]["email"] == "test@example.com"
    assert data["profile"]["full_name"] == "Test User"
    assert data["profile"]["business_name"] == "Test Business"
    
    # Check organization data
    assert data["organization"]["name"] == "Test Workspace"
    assert data["organization"]["website_url"] == "https://test.com"
    assert data["organization"]["support_email"] == "support@test.com"
    
    # Check notification settings
    assert data["notifications"]["email_notifications"] == True
    assert data["notifications"]["browser_notifications"] == False
    assert data["notifications"]["usage_alerts"] == True
    
    # Check appearance settings
    assert data["appearance"]["theme"] == "system"
    assert data["appearance"]["layout"] == "comfortable"
    assert data["appearance"]["language"] == "en"
    
    # Check team members
    assert len(data["team_members"]) == 1
    assert data["team_members"][0]["email"] == "member@example.com"
    assert data["team_members"][0]["role"] == "admin"


def test_get_settings_workspace_not_found(client, db_session, test_user, auth_token):
    """Test getting settings when workspace not found"""
    # Remove workspace
    db_session.delete(test_user.workspace_id)
    db_session.commit()
    
    response = client.get(
        "/api/v1/settings/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404


def test_update_profile_success(client, db_session, test_user, auth_token):
    """Test updating user profile successfully"""
    response = client.put(
        "/api/v1/settings/profile",
        json={
            "username": "newusername",
            "email": "newemail@example.com",
            "full_name": "New Full Name",
            "business_name": "New Business",
            "business_domain": "newbusiness.com",
            "profile_picture_url": "https://example.com/avatar.jpg"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newusername"
    assert data["email"] == "newemail@example.com"
    assert data["full_name"] == "New Full Name"
    
    # Verify database was updated
    db_session.refresh(test_user)
    assert test_user.username == "newusername"
    assert test_user.email == "newemail@example.com"


def test_update_profile_username_taken(client, db_session, test_user, auth_token):
    """Test updating profile with taken username"""
    # Create another user with the username we want to use
    other_user = User(
        id="other-user-id",
        email="other@example.com",
        username="takenusername",
        hashed_password="hashed_password",
        workspace_id="other-workspace"
    )
    db_session.add(other_user)
    db_session.commit()
    
    response = client.put(
        "/api/v1/settings/profile",
        json={
            "username": "takenusername",
            "email": test_user.email,
            "full_name": test_user.full_name,
            "business_name": test_user.business_name,
            "business_domain": test_user.business_domain
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Username already taken" in data["detail"]


def test_update_profile_email_taken(client, db_session, test_user, auth_token):
    """Test updating profile with taken email"""
    # Create another user with the email we want to use
    other_user = User(
        id="other-user-id",
        email="taken@example.com",
        username="otheruser",
        hashed_password="hashed_password",
        workspace_id="other-workspace"
    )
    db_session.add(other_user)
    db_session.commit()
    
    response = client.put(
        "/api/v1/settings/profile",
        json={
            "username": test_user.username,
            "email": "taken@example.com",
            "full_name": test_user.full_name,
            "business_name": test_user.business_name,
            "business_domain": test_user.business_domain
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Email already taken" in data["detail"]


def test_change_password_success(client, db_session, test_user, auth_token):
    """Test changing password successfully"""
    with patch('app.utils.password.verify_password', return_value=True):
        response = client.put(
            "/api/v1/settings/password",
            json={
                "current_password": "oldpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Password updated successfully" in data["message"]


def test_change_password_wrong_current(client, db_session, test_user, auth_token):
    """Test changing password with wrong current password"""
    with patch('app.utils.password.verify_password', return_value=False):
        response = client.put(
            "/api/v1/settings/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Current password is incorrect" in data["detail"]


def test_update_organization_success(client, db_session, test_user, test_workspace, auth_token):
    """Test updating organization settings successfully"""
    response = client.put(
        "/api/v1/settings/organization",
        json={
            "name": "Updated Workspace",
            "description": "Updated description",
            "website_url": "https://updated.com",
            "support_email": "support@updated.com",
            "logo_url": "https://example.com/logo.png",
            "custom_domain": "custom.updated.com",
            "widget_domain": "widget.updated.com",
            "timezone": "America/New_York"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Workspace"
    assert data["website_url"] == "https://updated.com"
    assert data["timezone"] == "America/New_York"
    
    # Verify database was updated
    db_session.refresh(test_workspace)
    assert test_workspace.name == "Updated Workspace"
    assert test_workspace.website_url == "https://updated.com"


def test_update_organization_workspace_not_found(client, db_session, test_user, auth_token):
    """Test updating organization when workspace not found"""
    # Remove workspace
    db_session.delete(test_user.workspace_id)
    db_session.commit()
    
    response = client.put(
        "/api/v1/settings/organization",
        json={
            "name": "Updated Workspace",
            "description": "Updated description"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404


def test_invite_team_member_success(client, db_session, test_user, auth_token):
    """Test inviting team member successfully"""
    response = client.post(
        "/api/v1/settings/team/invite",
        json={
            "email": "newmember@example.com",
            "role": "admin"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Invitation sent successfully" in data["message"]
    assert "invitation_token" in data
    
    # Verify team member was created
    team_member = db_session.query(TeamMember).filter(
        TeamMember.workspace_id == test_user.workspace_id,
        TeamMember.email == "newmember@example.com"
    ).first()
    assert team_member is not None
    assert team_member.role == "admin"
    assert team_member.status == "pending"


def test_invite_team_member_already_exists(client, db_session, test_user, auth_token):
    """Test inviting team member who already exists"""
    # Create existing team member
    existing_member = TeamMember(
        workspace_id=test_user.workspace_id,
        email="existing@example.com",
        role="admin",
        status="active"
    )
    db_session.add(existing_member)
    db_session.commit()
    
    response = client.post(
        "/api/v1/settings/team/invite",
        json={
            "email": "existing@example.com",
            "role": "admin"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already a member of this workspace" in data["detail"]


def test_get_team_members(client, db_session, test_user, auth_token):
    """Test getting team members"""
    # Add team members
    member1 = TeamMember(
        workspace_id=test_user.workspace_id,
        email="member1@example.com",
        full_name="Member One",
        role="admin",
        status="active",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    member2 = TeamMember(
        workspace_id=test_user.workspace_id,
        email="member2@example.com",
        full_name="Member Two",
        role="user",
        status="pending",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db_session.add_all([member1, member2])
    db_session.commit()
    
    response = client.get(
        "/api/v1/settings/team",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check member details
    member1_data = next(m for m in data if m["email"] == "member1@example.com")
    assert member1_data["full_name"] == "Member One"
    assert member1_data["role"] == "admin"
    assert member1_data["status"] == "active"


def test_update_notifications(client, db_session, test_user, auth_token):
    """Test updating notification preferences"""
    response = client.put(
        "/api/v1/settings/notifications",
        json={
            "email_notifications": False,
            "browser_notifications": True,
            "usage_alerts": False,
            "billing_updates": True,
            "security_alerts": True,
            "product_updates": True
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email_notifications"] == False
    assert data["browser_notifications"] == True
    assert data["usage_alerts"] == False
    
    # Verify database was updated
    db_session.refresh(test_user)
    assert test_user.email_notifications == False
    assert test_user.browser_notifications == True


def test_update_appearance(client, db_session, test_user, auth_token):
    """Test updating appearance preferences"""
    response = client.put(
        "/api/v1/settings/appearance",
        json={
            "theme": "dark",
            "layout": "compact",
            "language": "es",
            "timezone": "Europe/London"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["layout"] == "compact"
    assert data["language"] == "es"
    assert data["timezone"] == "Europe/London"
    
    # Verify database was updated
    db_session.refresh(test_user)
    assert test_user.theme == "dark"
    assert test_user.layout == "compact"


def test_setup_two_factor(client, db_session, test_user, auth_token):
    """Test setting up two-factor authentication"""
    with patch('pyotp.random_base32', return_value="testsecret"), \
         patch('pyotp.TOTP') as mock_totp, \
         patch('qrcode.QRCode') as mock_qr:
        
        mock_totp_instance = Mock()
        mock_totp_instance.provisioning_uri.return_value = "otpauth://totp/test@example.com?secret=testsecret&issuer=CustomerCareGPT"
        mock_totp.return_value = mock_totp_instance
        
        mock_qr_instance = Mock()
        mock_qr_instance.make_image.return_value = Mock()
        mock_qr.return_value = mock_qr_instance
        
        response = client.post(
            "/api/v1/settings/2fa/setup",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 10
        
        # Verify secret was stored
        db_session.refresh(test_user)
        assert test_user.two_factor_secret == "testsecret"


def test_verify_two_factor(client, db_session, test_user, auth_token):
    """Test verifying two-factor authentication"""
    # Setup 2FA first
    test_user.two_factor_secret = "testsecret"
    db_session.commit()
    
    with patch('pyotp.TOTP') as mock_totp:
        mock_totp_instance = Mock()
        mock_totp_instance.verify.return_value = True
        mock_totp.return_value = mock_totp_instance
        
        response = client.post(
            "/api/v1/settings/2fa/verify",
            params={"code": "123456"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Two-factor authentication enabled successfully" in data["message"]
        
        # Verify 2FA was enabled
        db_session.refresh(test_user)
        assert test_user.two_factor_enabled == True


def test_verify_two_factor_invalid_code(client, db_session, test_user, auth_token):
    """Test verifying two-factor authentication with invalid code"""
    test_user.two_factor_secret = "testsecret"
    db_session.commit()
    
    with patch('pyotp.TOTP') as mock_totp:
        mock_totp_instance = Mock()
        mock_totp_instance.verify.return_value = False
        mock_totp.return_value = mock_totp_instance
        
        response = client.post(
            "/api/v1/settings/2fa/verify",
            params={"code": "000000"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid verification code" in data["detail"]


def test_upload_profile_picture(client, db_session, test_user, auth_token):
    """Test uploading profile picture"""
    # Create a mock image file
    image_content = b"fake_image_content"
    
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.makedirs') as mock_makedirs:
        
        mock_file = Mock()
        mock_file.read.return_value = image_content
        mock_file.content_type = "image/jpeg"
        mock_file.size = len(image_content)
        mock_file.filename = "avatar.jpg"
        
        response = client.post(
            "/api/v1/settings/upload/profile-picture",
            files={"file": ("avatar.jpg", image_content, "image/jpeg")},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "filename" in data
        assert data["size"] == len(image_content)
        assert data["content_type"] == "image/jpeg"


def test_upload_profile_picture_invalid_type(client, db_session, test_user, auth_token):
    """Test uploading non-image file as profile picture"""
    text_content = b"not an image"
    
    response = client.post(
        "/api/v1/settings/upload/profile-picture",
        files={"file": ("document.txt", text_content, "text/plain")},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "File must be an image" in data["detail"]


def test_upload_organization_logo(client, db_session, test_user, test_workspace, auth_token):
    """Test uploading organization logo"""
    image_content = b"fake_logo_content"
    
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.makedirs') as mock_makedirs:
        
        mock_file = Mock()
        mock_file.read.return_value = image_content
        mock_file.content_type = "image/png"
        mock_file.size = len(image_content)
        mock_file.filename = "logo.png"
        
        response = client.post(
            "/api/v1/settings/upload/organization-logo",
            files={"file": ("logo.png", image_content, "image/png")},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "filename" in data
        assert data["content_type"] == "image/png"
        
        # Verify workspace logo was updated
        db_session.refresh(test_workspace)
        assert test_workspace.logo_url is not None

