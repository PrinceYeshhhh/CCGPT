"""
Embed code service for generating widget scripts
"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import structlog

from app.models.embed import EmbedCode
from app.core.config import settings

logger = structlog.get_logger()


class EmbedService:
    """Embed code service for managing widget scripts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_embed_code(
        self,
        user_id: int,
        code_name: str,
        widget_config: Dict[str, Any]
    ) -> EmbedCode:
        """Create a new embed code"""
        
        # Generate embed script
        embed_script = self._generate_embed_script(widget_config)
        embed_html = self._generate_embed_html(widget_config)
        
        # Create embed code record
        embed_code = EmbedCode(
            user_id=user_id,
            code_name=code_name,
            widget_config=widget_config,
            embed_script=embed_script,
            embed_html=embed_html,
            is_active=True
        )
        
        self.db.add(embed_code)
        self.db.commit()
        self.db.refresh(embed_code)
        
        return embed_code
    
    def get_user_embed_codes(self, user_id: int) -> List[EmbedCode]:
        """Get all embed codes for a user"""
        return self.db.query(EmbedCode).filter(
            EmbedCode.user_id == user_id
        ).order_by(EmbedCode.created_at.desc()).all()
    
    def get_embed_code_by_id(self, code_id: int, user_id: int) -> Optional[EmbedCode]:
        """Get embed code by ID for specific user"""
        return self.db.query(EmbedCode).filter(
            EmbedCode.id == code_id,
            EmbedCode.user_id == user_id
        ).first()
    
    def update_embed_code(
        self,
        code_id: int,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[EmbedCode]:
        """Update embed code"""
        embed_code = self.get_embed_code_by_id(code_id, user_id)
        if not embed_code:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(embed_code, field) and value is not None:
                setattr(embed_code, field, value)
        
        # Regenerate scripts if widget config changed
        if "widget_config" in update_data:
            embed_code.embed_script = self._generate_embed_script(embed_code.widget_config)
            embed_code.embed_html = self._generate_embed_html(embed_code.widget_config)
        
        self.db.commit()
        self.db.refresh(embed_code)
        return embed_code
    
    def delete_embed_code(self, code_id: int, user_id: int) -> bool:
        """Delete embed code"""
        embed_code = self.get_embed_code_by_id(code_id, user_id)
        if not embed_code:
            return False
        
        self.db.delete(embed_code)
        self.db.commit()
        return True
    
    def regenerate_embed_code(self, code_id: int, user_id: int) -> Optional[EmbedCode]:
        """Regenerate embed code scripts"""
        embed_code = self.get_embed_code_by_id(code_id, user_id)
        if not embed_code:
            return None
        
        # Regenerate scripts
        embed_code.embed_script = self._generate_embed_script(embed_code.widget_config)
        embed_code.embed_html = self._generate_embed_html(embed_code.widget_config)
        
        self.db.commit()
        self.db.refresh(embed_code)
        return embed_code
    
    def get_widget_script(self, code_id: int) -> Optional[str]:
        """Get widget script for public access"""
        embed_code = self.db.query(EmbedCode).filter(
            EmbedCode.id == code_id,
            EmbedCode.is_active == True
        ).first()
        
        if not embed_code:
            return None
        
        return embed_code.embed_script
    
    def increment_usage(self, code_id: int):
        """Increment usage count for embed code"""
        embed_code = self.db.query(EmbedCode).filter(
            EmbedCode.id == code_id
        ).first()
        
        if embed_code:
            embed_code.usage_count += 1
            embed_code.last_used = func.now()
            self.db.commit()
    
    def _generate_embed_script(self, config: Dict[str, Any]) -> str:
        """Generate JavaScript embed script"""
        script_template = f"""
(function() {{
    // CustomerCareGPT Widget
    const config = {{
        apiUrl: '{settings.API_BASE_URL or "http://localhost:8000"}',
        codeId: '{config.get("code_id", "")}',
        title: '{config.get("title", "Customer Support")}',
        placeholder: '{config.get("placeholder", "Ask me anything...")}',
        primaryColor: '{config.get("primary_color", "#007bff")}',
        position: '{config.get("position", "bottom-right")}',
        showAvatar: {str(config.get("show_avatar", True)).lower()},
        avatarUrl: '{config.get("avatar_url", "")}',
        welcomeMessage: '{config.get("welcome_message", "Hello! How can I help you today?")}',
        maxMessages: {config.get("max_messages", 50)},
        enableSound: {str(config.get("enable_sound", True)).lower()},
        enableTypingIndicator: {str(config.get("enable_typing_indicator", True)).lower()}
    }};
    
    // Widget HTML
    const widgetHTML = `
        <div id="ccgpt-widget" style="
            position: fixed;
            {self._get_position_css(config.get("position", "bottom-right"))}
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div id="ccgpt-chat-container" style="
                display: none;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
                flex-direction: column;
            ">
                <div id="ccgpt-header" style="
                    background: ${{config.primaryColor}};
                    color: white;
                    padding: 16px;
                    border-radius: 12px 12px 0 0;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <div style="display: flex; align-items: center;">
                        {self._get_avatar_html(config)}
                        <span style="margin-left: 8px; font-weight: 600;">${{config.title}}</span>
                    </div>
                    <button id="ccgpt-close" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 18px;
                        cursor: pointer;
                        padding: 4px;
                    ">×</button>
                </div>
                
                <div id="ccgpt-messages" style="
                    flex: 1;
                    padding: 16px;
                    overflow-y: auto;
                    background: #f8f9fa;
                ">
                    <div class="ccgpt-message ccgpt-bot" style="
                        background: white;
                        padding: 12px;
                        border-radius: 8px;
                        margin-bottom: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        ${{config.welcomeMessage}}
                    </div>
                </div>
                
                <div id="ccgpt-input-container" style="
                    padding: 16px;
                    background: white;
                    border-top: 1px solid #e0e0e0;
                    border-radius: 0 0 12px 12px;
                ">
                    <div style="display: flex; gap: 8px;">
                        <input id="ccgpt-input" type="text" placeholder="${{config.placeholder}}" style="
                            flex: 1;
                            padding: 12px;
                            border: 1px solid #ddd;
                            border-radius: 20px;
                            outline: none;
                            font-size: 14px;
                        ">
                        <button id="ccgpt-send" style="
                            background: ${{config.primaryColor}};
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">→</button>
                    </div>
                </div>
            </div>
            
            <button id="ccgpt-toggle" style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: ${{config.primaryColor}};
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            ">
                💬
            </button>
        </div>
    `;
    
    // Add widget to page
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    
    // Widget functionality
    const widget = document.getElementById('ccgpt-widget');
    const chatContainer = document.getElementById('ccgpt-chat-container');
    const toggle = document.getElementById('ccgpt-toggle');
    const close = document.getElementById('ccgpt-close');
    const input = document.getElementById('ccgpt-input');
    const send = document.getElementById('ccgpt-send');
    const messages = document.getElementById('ccgpt-messages');
    
    let isOpen = false;
    let messageCount = 0;
    
    // Toggle chat
    toggle.addEventListener('click', () => {{
        isOpen = !isOpen;
        chatContainer.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) input.focus();
    }});
    
    // Close chat
    close.addEventListener('click', () => {{
        isOpen = false;
        chatContainer.style.display = 'none';
    }});
    
    // Send message
    const sendMessage = async () => {{
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        try {{
            const response = await fetch(`${{config.apiUrl}}/api/v1/chat/message`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    message: message,
                    code_id: config.codeId
                }})
            }});
            
            const data = await response.json();
            hideTypingIndicator();
            addMessage(data.message.content, 'bot');
            
        }} catch (error) {{
            hideTypingIndicator();
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }}
    }};
    
    // Event listeners
    send.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {{
        if (e.key === 'Enter') sendMessage();
    }});
    
    // Helper functions
    function addMessage(content, type) {{
        if (messageCount >= config.maxMessages) {{
            messages.removeChild(messages.firstChild);
        }} else {{
            messageCount++;
        }}
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ccgpt-message ccgpt-${{type}}`;
        messageDiv.style.cssText = `
            background: ${{type === 'user' ? config.primaryColor : 'white'}};
            color: ${{type === 'user' ? 'white' : 'black'}};
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-left: ${{type === 'user' ? '20px' : '0'}};
            margin-right: ${{type === 'bot' ? '20px' : '0'}};
        `;
        messageDiv.textContent = content;
        
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }}
    
    function showTypingIndicator() {{
        const typingDiv = document.createElement('div');
        typingDiv.id = 'ccgpt-typing';
        typingDiv.className = 'ccgpt-message ccgpt-bot';
        typingDiv.style.cssText = `
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #666;
        `;
        typingDiv.textContent = 'Typing...';
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
    }}
    
    function hideTypingIndicator() {{
        const typing = document.getElementById('ccgpt-typing');
        if (typing) typing.remove();
    }}
}})();
"""
        return script_template.strip()
    
    def _generate_embed_html(self, config: Dict[str, Any]) -> str:
        """Generate HTML embed code"""
        return f"""
<!-- CustomerCareGPT Widget -->
<script>
{self._generate_embed_script(config)}
</script>
"""
    
    def _get_position_css(self, position: str) -> str:
        """Get CSS for widget position"""
        positions = {
            "bottom-right": "bottom: 20px; right: 20px;",
            "bottom-left": "bottom: 20px; left: 20px;",
            "top-right": "top: 20px; right: 20px;",
            "top-left": "top: 20px; left: 20px;"
        }
        return positions.get(position, positions["bottom-right"])
    
    def _get_avatar_html(self, config: Dict[str, Any]) -> str:
        """Get avatar HTML"""
        if not config.get("show_avatar", True):
            return ""
        
        avatar_url = config.get("avatar_url", "")
        if avatar_url:
            return f'<img src="{avatar_url}" style="width: 24px; height: 24px; border-radius: 50%;">'
        else:
            return '<div style="width: 24px; height: 24px; border-radius: 50%; background: rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 12px;">🤖</div>'
