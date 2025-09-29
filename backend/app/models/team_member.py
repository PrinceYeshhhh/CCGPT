"""
Team member model for workspace collaboration
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.uuid_type import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TeamMember(Base):
    """Team member model for workspace collaboration"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="member")  # member, admin, owner
    status = Column(String(20), default="pending")  # pending, active, inactive
    invitation_token = Column(String(128), nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="team_members")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<TeamMember(id={self.id}, email='{self.email}', role='{self.role}')>"
