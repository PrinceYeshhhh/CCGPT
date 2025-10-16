"""
User service
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.password import get_password_hash


class UserService:
    """User service for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_mobile(self, mobile_phone: str) -> Optional[User]:
        """Get user by mobile phone number"""
        return self.db.query(User).filter(User.mobile_phone == mobile_phone).first()
    
    def create_user(self, user_data: UserCreate, phone_verified: bool = False, workspace_id: str = None) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        
        # If workspace_id is provided via user_data (testing mode), use it
        if hasattr(user_data, 'workspace_id') and user_data.workspace_id:
            workspace_id = user_data.workspace_id
        
        # If no workspace_id provided, create a default one (for testing)
        if not workspace_id:
            from app.models.workspace import Workspace
            import uuid
            workspace = self.db.query(Workspace).first()
            if not workspace:
                workspace = Workspace(
                    id=str(uuid.uuid4()),
                    name="Default Workspace",
                    domain="default.example.com"
                )
                self.db.add(workspace)
                self.db.commit()
                self.db.refresh(workspace)
            workspace_id = workspace.id
        
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            business_name=user_data.business_name,
            business_domain=user_data.business_domain,
            mobile_phone=user_data.mobile_phone,
            phone_verified=phone_verified,
            workspace_id=workspace_id
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user(self, user_id: int, user_data: dict) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for field, value in user_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
