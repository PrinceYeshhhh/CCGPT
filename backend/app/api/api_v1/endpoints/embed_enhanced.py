"""
Enhanced embed endpoints for widget generation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.embed import (
    EmbedCodeGenerateRequest,
    EmbedCodeGenerateResponse,
    EmbedCodeResponse,
    EmbedCodeUpdate,
    WidgetConfig,
    WidgetPreviewRequest,
    WidgetPreviewResponse,
    WidgetAssetCreate,
    WidgetAssetResponse
)
from app.services.auth import AuthService
from app.services.embed_service import EmbedService
from app.services.rate_limiting import rate_limiting_service
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.post("/generate", response_model=EmbedCodeGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_embed_code(
    request: EmbedCodeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new embed code with API key"""
    try:
        embed_service = EmbedService(db)
        
        # Convert config to dict if provided
        config_dict = request.config.dict() if request.config else None
        
        # Generate embed code
        embed_code = embed_service.generate_embed_code(
            workspace_id=request.workspace_id,
            user_id=current_user.id,
            code_name=request.code_name,
            config=config_dict,
            snippet_template=request.snippet_template
        )
        
        # Generate embed snippet
        embed_snippet = embed_service.get_embed_snippet(embed_code)
        
        logger.info(
            "Embed code generated successfully",
            user_id=current_user.id,
            embed_code_id=embed_code.id,
            workspace_id=request.workspace_id
        )
        
        return EmbedCodeGenerateResponse(
            embed_code_id=embed_code.id,
            client_api_key=embed_code.client_api_key,
            embed_snippet=embed_snippet,
            widget_url=f"{request.workspace_id}/widget/{embed_code.id}",
            config=WidgetConfig(**embed_code.default_config)
        )
        
    except Exception as e:
        logger.error(
            "Embed code generation failed",
            error=str(e),
            user_id=current_user.id,
            workspace_id=request.workspace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embed code"
        )


@router.get("/codes", response_model=List[EmbedCodeResponse])
async def get_embed_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's embed codes"""
    try:
        embed_service = EmbedService(db)
        embed_codes = embed_service.get_user_embed_codes(current_user.id)
        
        return [EmbedCodeResponse.from_orm(code) for code in embed_codes]
        
    except Exception as e:
        logger.error("Failed to get embed codes", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed codes"
        )


@router.get("/codes/{code_id}", response_model=EmbedCodeResponse)
async def get_embed_code(
    code_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific embed code"""
    try:
        embed_service = EmbedService(db)
        embed_code = embed_service.get_embed_code_by_id(code_id, current_user.id)
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        return EmbedCodeResponse.from_orm(embed_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed code"
        )


@router.put("/codes/{code_id}", response_model=EmbedCodeResponse)
async def update_embed_code(
    code_id: str,
    request: EmbedCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an embed code"""
    try:
        embed_service = EmbedService(db)
        
        # Convert config to dict if provided
        update_data = request.dict(exclude_unset=True)
        if "widget_config" in update_data:
            update_data["default_config"] = update_data.pop("widget_config")
        
        embed_code = embed_service.update_embed_code(
            code_id=code_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code updated successfully",
            user_id=current_user.id,
            code_id=code_id
        )
        
        return EmbedCodeResponse.from_orm(embed_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update embed code"
        )


@router.delete("/codes/{code_id}")
async def delete_embed_code(
    code_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an embed code"""
    try:
        embed_service = EmbedService(db)
        success = embed_service.delete_embed_code(code_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code deleted successfully",
            user_id=current_user.id,
            code_id=code_id
        )
        
        return {"message": "Embed code deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete embed code"
        )


@router.post("/codes/{code_id}/regenerate")
async def regenerate_embed_code(
    code_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate embed code script"""
    try:
        embed_service = EmbedService(db)
        embed_code = embed_service.regenerate_embed_code(code_id, current_user.id)
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code regenerated successfully",
            user_id=current_user.id,
            code_id=code_id
        )
        
        return {"message": "Embed code regenerated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to regenerate embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate embed code"
        )


@router.get("/widget/{code_id}")
async def get_widget_script(
    code_id: str,
    db: Session = Depends(get_db)
):
    """Get widget script for embedding (public endpoint)"""
    try:
        embed_service = EmbedService(db)
        script_content = embed_service.get_widget_script(code_id)
        
        if not script_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found or inactive"
            )
        
        # Update usage count
        embed_service.increment_usage(code_id)
        
        # Serve raw JavaScript for direct <script src> embedding
        return Response(content=script_content, media_type="application/javascript")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get widget script",
            error=str(e),
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget script"
        )


@router.post("/preview", response_model=WidgetPreviewResponse)
async def preview_widget(
    request: WidgetPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview widget with custom configuration"""
    try:
        embed_service = EmbedService(db)
        
        # Generate preview script
        config_dict = request.config.dict()
        preview_script = embed_service._generate_embed_script(
            embed_code_id="preview",
            client_api_key="preview",
            config=config_dict
        )
        
        # Generate preview HTML
        preview_html = embed_service._generate_embed_html(preview_script)
        
        # Generate preview CSS
        preview_css = f"""
:root {{
    --ccgpt-primary: {config_dict.get('primary_color', '#4f46e5')};
    --ccgpt-secondary: {config_dict.get('secondary_color', '#f8f9fa')};
    --ccgpt-text: {config_dict.get('text_color', '#111111')};
}}
"""
        
        return WidgetPreviewResponse(
            preview_html=preview_html,
            preview_css=preview_css,
            preview_js=preview_script
        )
        
    except Exception as e:
        logger.error(
            "Failed to generate widget preview",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate widget preview"
        )


@router.post("/chat/message")
async def widget_chat_message(
    request: dict,
    db: Session = Depends(get_db),
    x_client_api_key: Optional[str] = Header(None, alias="X-Client-API-Key"),
    x_embed_code_id: Optional[str] = Header(None, alias="X-Embed-Code-ID"),
    origin: Optional[str] = Header(None, alias="Origin"),
    referer: Optional[str] = Header(None, alias="Referer"),
    http_request: Request = None
):
    """Handle chat messages from widget (with API key authentication)"""
    try:
        # Determine client IP
        client_ip = http_request.client.host if http_request and http_request.client else "unknown"
        
        # Validate and sanitize input
        if not request or not isinstance(request, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format"
            )
        
        # Sanitize message content
        message = request.get("message", "")
        if not message or not isinstance(message, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required and must be a string"
            )
        
        # Remove potentially dangerous content
        import re
        message = re.sub(r'<script[^>]*>.*?</script>', '', message, flags=re.IGNORECASE | re.DOTALL)
        message = re.sub(r'javascript:', '', message, flags=re.IGNORECASE)
        message = message.strip()
        
        if len(message) > 1000:  # Limit message length
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long"
            )

        # Rate limiting check
        is_allowed, rate_limit_info = await rate_limiting_service.check_ip_rate_limit(
            ip_address=client_ip,
            limit=10,  # 10 requests per minute per IP
            window_seconds=60
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                    "X-RateLimit-Reset": str(int(rate_limit_info["reset_time"].timestamp()))
                }
            )
        
        # Authenticate using API key
        if not x_client_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client API key required"
            )
        
        embed_service = EmbedService(db)
        embed_code = embed_service.get_embed_code_by_api_key(x_client_api_key)
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client API key"
            )
        
        # Verify embed code ID matches
        if x_embed_code_id and str(embed_code.id) != x_embed_code_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid embed code ID"
            )
        
        # Verify embed code is active and not expired
        if not embed_code.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Embed code is inactive"
            )
        
        # Check if embed code has expired
        if embed_code.expires_at and embed_code.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Embed code has expired"
            )

        # Per-embed rate limit
        is_allowed_embed, embed_rl = await rate_limiting_service.check_rate_limit(
            identifier=f"embed:{embed_code.id}",
            limit=60,
            window_seconds=60
        )
        if not is_allowed_embed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Embed rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(embed_rl.get("limit", 60)),
                    "X-RateLimit-Remaining": str(embed_rl.get("remaining", 0)),
                    "X-RateLimit-Reset": str(int(embed_rl.get("reset_time").timestamp())) if embed_rl.get("reset_time") else "0"
                }
            )

        # Per-workspace rate limit
        is_allowed_ws, ws_rl = await rate_limiting_service.check_workspace_rate_limit(
            workspace_id=str(embed_code.workspace_id),
            limit=120,
            window_seconds=60
        )
        if not is_allowed_ws:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Workspace rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(ws_rl.get("limit", 120)),
                    "X-RateLimit-Remaining": str(ws_rl.get("remaining", 0)),
                    "X-RateLimit-Reset": str(int(ws_rl.get("reset_time").timestamp())) if ws_rl.get("reset_time") else "0"
                }
            )
        
        # Validate CORS origin if configured
        if hasattr(embed_code, 'allowed_origins') and embed_code.allowed_origins:
            allowed_origins = embed_code.allowed_origins.split(',')
            if origin and origin not in allowed_origins:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Origin not allowed"
                )
        
        # Process the chat message using existing chat service
        from app.services.chat import ChatService
        chat_service = ChatService(db)
        
        response = await chat_service.process_message(
            user_id=embed_code.user_id,
            message=message,  # Use sanitized message
            session_id=request.get("session_id"),
            context={"embed_code_id": str(embed_code.id), "workspace_id": str(embed_code.workspace_id)}
        )
        
        # Update usage count
        embed_service.increment_usage(str(embed_code.id))
        
        logger.info(
            "Widget chat message processed",
            embed_code_id=embed_code.id,
            workspace_id=str(embed_code.workspace_id),
            client_ip=client_ip
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Widget chat message failed",
            error=str(e),
            client_ip=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
