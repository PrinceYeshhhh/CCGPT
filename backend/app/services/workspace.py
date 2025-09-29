"""
Workspace management service
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import structlog

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.core.database import WriteSessionLocal as SessionLocal

logger = structlog.get_logger()


class WorkspaceService:
    """Service for workspace management operations"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def create_workspace(self, workspace_data: WorkspaceCreate, user_id: int) -> Workspace:
        """Create a new workspace"""
        try:
            workspace = Workspace(
                name=workspace_data.name,
                description=workspace_data.description,
                owner_id=user_id,
                settings=workspace_data.settings or {}
            )
            
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
            
            logger.info("Workspace created", workspace_id=workspace.id, user_id=user_id)
            return workspace
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create workspace", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workspace"
            )
    
    def get_workspace(self, workspace_id: int, user_id: int) -> Optional[Workspace]:
        """Get workspace by ID"""
        try:
            workspace = self.db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.owner_id == user_id
            ).first()
            
            if not workspace:
                logger.warning("Workspace not found", workspace_id=workspace_id, user_id=user_id)
                return None
                
            return workspace
            
        except Exception as e:
            logger.error("Failed to get workspace", error=str(e), workspace_id=workspace_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get workspace"
            )
    
    def get_user_workspaces(self, user_id: int) -> List[Workspace]:
        """Get all workspaces for a user"""
        try:
            workspaces = self.db.query(Workspace).filter(
                Workspace.owner_id == user_id
            ).all()
            
            return workspaces
            
        except Exception as e:
            logger.error("Failed to get user workspaces", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get workspaces"
            )
    
    def update_workspace(self, workspace_id: int, workspace_data: WorkspaceUpdate, user_id: int) -> Optional[Workspace]:
        """Update workspace"""
        try:
            workspace = self.get_workspace(workspace_id, user_id)
            if not workspace:
                return None
            
            if workspace_data.name is not None:
                workspace.name = workspace_data.name
            if workspace_data.description is not None:
                workspace.description = workspace_data.description
            if workspace_data.settings is not None:
                workspace.settings = workspace_data.settings
            
            self.db.commit()
            self.db.refresh(workspace)
            
            logger.info("Workspace updated", workspace_id=workspace_id, user_id=user_id)
            return workspace
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update workspace", error=str(e), workspace_id=workspace_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update workspace"
            )
    
    def delete_workspace(self, workspace_id: int, user_id: int) -> bool:
        """Delete workspace"""
        try:
            workspace = self.get_workspace(workspace_id, user_id)
            if not workspace:
                return False
            
            self.db.delete(workspace)
            self.db.commit()
            
            logger.info("Workspace deleted", workspace_id=workspace_id, user_id=user_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete workspace", error=str(e), workspace_id=workspace_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete workspace"
            )
    
    def get_workspace_settings(self, workspace_id: int, user_id: int) -> Dict[str, Any]:
        """Get workspace settings"""
        workspace = self.get_workspace(workspace_id, user_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        return workspace.settings or {}
    
    def update_workspace_settings(self, workspace_id: int, settings: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Update workspace settings"""
        try:
            workspace = self.get_workspace(workspace_id, user_id)
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            
            workspace.settings = settings
            self.db.commit()
            self.db.refresh(workspace)
            
            logger.info("Workspace settings updated", workspace_id=workspace_id, user_id=user_id)
            return workspace.settings
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update workspace settings", error=str(e), workspace_id=workspace_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update workspace settings"
            )
