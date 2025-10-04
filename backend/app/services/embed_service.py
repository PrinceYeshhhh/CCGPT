"""
Enhanced embed service for widget generation and management
"""

import uuid
import secrets
import hashlib
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import structlog

from app.models.embed import EmbedCode, WidgetAsset
from app.core.config import settings
from app.services.ab_testing_service import ABTestingService

logger = structlog.get_logger()


class EmbedService:
    """Enhanced embed service for managing widget scripts and generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ab_testing_service = ABTestingService(db)
    
    def generate_embed_code(
        self,
        workspace_id: str,
        user_id: int,
        code_name: str,
        config: Optional[Dict[str, Any]] = None,
        snippet_template: Optional[str] = None
    ) -> EmbedCode:
        """Generate a new embed code with API key"""
        
        # Generate client API key
        client_api_key = self._generate_client_api_key(workspace_id)
        
        # Default configuration
        default_config = {
            "title": "Customer Support",
            "placeholder": "Ask me anything...",
            "primary_color": "#4f46e5",
            "secondary_color": "#f8f9fa",
            "text_color": "#111111",
            "position": "bottom-right",
            "show_avatar": True,
            "avatar_url": None,
            "welcome_message": "Hello! How can I help you today?",
            "max_messages": 50,
            "enable_sound": True,
            "enable_typing_indicator": True,
            "enable_websocket": True,
            "theme": "light",
            "custom_css": None
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        # Apply A/B testing variants if enabled
        if settings.AB_TESTING_ENABLED:
            default_config = self.ab_testing_service.apply_variants_to_config(
                default_config, 
                str(user_id)
            )
        
        # Generate embed script
        embed_script = self._generate_embed_script(
            embed_code_id=str(uuid.uuid4()),
            client_api_key=client_api_key,
            config=default_config,
            snippet_template=snippet_template
        )
        
        # Generate embed HTML
        embed_html = self._generate_embed_html(embed_script)
        
        # Create embed code record
        embed_code = EmbedCode(
            workspace_id=uuid.UUID(workspace_id),
            user_id=user_id,
            code_name=code_name,
            client_api_key=client_api_key,
            snippet_template=snippet_template,
            default_config=default_config,
            embed_script=embed_script,
            embed_html=embed_html,
            is_active=True
        )
        
        self.db.add(embed_code)
        self.db.commit()
        self.db.refresh(embed_code)
        
        logger.info(
            "Embed code generated",
            embed_code_id=embed_code.id,
            workspace_id=workspace_id,
            user_id=user_id
        )
        
        return embed_code
    
    def get_embed_code_by_api_key(self, client_api_key: str) -> Optional[EmbedCode]:
        """Get embed code by client API key"""
        return self.db.query(EmbedCode).filter(
            EmbedCode.client_api_key == client_api_key,
            EmbedCode.is_active == True
        ).first()
    
    def get_embed_code_by_id(self, code_id: str, user_id: int) -> Optional[EmbedCode]:
        """Get embed code by ID for specific user"""
        return self.db.query(EmbedCode).filter(
            EmbedCode.id == uuid.UUID(code_id),
            EmbedCode.user_id == user_id
        ).first()
    
    def get_user_embed_codes(self, user_id: int) -> List[EmbedCode]:
        """Get all embed codes for a user"""
        return self.db.query(EmbedCode).filter(
            EmbedCode.user_id == user_id
        ).order_by(EmbedCode.created_at.desc()).all()
    
    def update_embed_code(
        self,
        code_id: str,
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
        
        # Regenerate scripts if config changed
        if "default_config" in update_data or "custom_config" in update_data:
            config = embed_code.default_config.copy()
            if embed_code.custom_config:
                config.update(embed_code.custom_config)
            
            embed_code.embed_script = self._generate_embed_script(
                embed_code_id=str(embed_code.id),
                client_api_key=embed_code.client_api_key,
                config=config,
                snippet_template=embed_code.snippet_template
            )
            embed_code.embed_html = self._generate_embed_html(embed_code.embed_script)
        
        self.db.commit()
        self.db.refresh(embed_code)
        return embed_code
    
    def delete_embed_code(self, code_id: str, user_id: int) -> bool:
        """Delete embed code"""
        embed_code = self.get_embed_code_by_id(code_id, user_id)
        if not embed_code:
            return False
        
        self.db.delete(embed_code)
        self.db.commit()
        return True
    
    def regenerate_embed_code(self, code_id: str, user_id: int) -> Optional[EmbedCode]:
        """Regenerate embed code scripts"""
        embed_code = self.get_embed_code_by_id(code_id, user_id)
        if not embed_code:
            return None
        
        # Regenerate scripts
        config = embed_code.default_config.copy()
        if embed_code.custom_config:
            config.update(embed_code.custom_config)
        
        embed_code.embed_script = self._generate_embed_script(
            embed_code_id=str(embed_code.id),
            client_api_key=embed_code.client_api_key,
            config=config,
            snippet_template=embed_code.snippet_template
        )
        embed_code.embed_html = self._generate_embed_html(embed_code.embed_script)
        
        self.db.commit()
        self.db.refresh(embed_code)
        return embed_code
    
    def get_widget_script(self, code_id: str) -> Optional[str]:
        """Get widget script for public access"""
        embed_code = self.db.query(EmbedCode).filter(
            EmbedCode.id == uuid.UUID(code_id),
            EmbedCode.is_active == True
        ).first()
        
        if not embed_code:
            return None
        
        return embed_code.embed_script
    
    def increment_usage(self, code_id: str):
        """Increment usage count for embed code"""
        embed_code = self.db.query(EmbedCode).filter(
            EmbedCode.id == uuid.UUID(code_id)
        ).first()
        
        if embed_code:
            embed_code.usage_count += 1
            embed_code.last_used = func.now()
            self.db.commit()
    
    def _generate_client_api_key(self, workspace_id: str) -> str:
        """Generate a secure client API key"""
        # Create a unique key based on workspace and random data
        random_data = secrets.token_hex(16)
        key_data = f"{workspace_id}:{random_data}:{uuid.uuid4()}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _generate_embed_script(
        self,
        embed_code_id: str,
        client_api_key: str,
        config: Dict[str, Any],
        snippet_template: Optional[str] = None
    ) -> str:
        """Generate enhanced JavaScript embed script"""
        
        if snippet_template:
            # Use custom template
            return snippet_template.format(
                embed_code_id=embed_code_id,
                client_api_key=client_api_key,
                config=config,
                api_url=settings.API_BASE_URL
            )
        
        # Default enhanced template
        return f"""
(function() {{
    'use strict';
    
    // Configuration
    const CONFIG = {{
        apiUrl: '{settings.API_BASE_URL}',
        embedCodeId: '{embed_code_id}',
        clientApiKey: '{client_api_key}',
        title: '{config.get("title", "Customer Support")}',
        placeholder: '{config.get("placeholder", "Ask me anything...")}',
        primaryColor: '{config.get("primary_color", "#4f46e5")}',
        secondaryColor: '{config.get("secondary_color", "#f8f9fa")}',
        textColor: '{config.get("text_color", "#111111")}',
        position: '{config.get("position", "bottom-right")}',
        showAvatar: {str(config.get("show_avatar", True)).lower()},
        avatarUrl: '{config.get("avatar_url", "")}',
        welcomeMessage: '{config.get("welcome_message", "Hello! How can I help you today?")}',
        maxMessages: {config.get("max_messages", 50)},
        enableSound: {str(config.get("enable_sound", True)).lower()},
        enableTypingIndicator: {str(config.get("enable_typing_indicator", True)).lower()},
        enableWebSocket: {str(config.get("enable_websocket", True)).lower()},
        theme: '{config.get("theme", "light")}',
        customCss: `{config.get("custom_css", "")}`,
        zIndex: 10000
    }};
    
    // State
    let isOpen = false;
    let messageCount = 0;
    let sessionId = null;
    let widget = null;
    let chatContainer = null;
    let messagesContainer = null;
    let input = null;
    let sendButton = null;
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    // Initialize widget
    function init() {{
        createWidget();
        attachEventListeners();
        loadSession();
        
        // Try WebSocket connection if enabled
        if (CONFIG.enableWebSocket) {{
            connectWebSocket();
        }}
    }}
    
    // Create widget HTML
    function createWidget() {{
        const widgetHTML = `
            <div id="ccgpt-widget" style="
                position: fixed;
                ${{getPositionCSS()}}
                z-index: ${{CONFIG.zIndex}};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <div id="ccgpt-chat-container" style="
                    display: none;
                    width: 350px;
                    height: 500px;
                    background: ${{CONFIG.secondaryColor}};
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    border: 1px solid #e0e0e0;
                    flex-direction: column;
                ">
                    <div id="ccgpt-header" style="
                        background: ${{CONFIG.primaryColor}};
                        color: white;
                        padding: 16px;
                        border-radius: 12px 12px 0 0;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <div style="display: flex; align-items: center;">
                            ${{getAvatarHTML()}}
                            <span style="margin-left: 8px; font-weight: 600;">${{CONFIG.title}}</span>
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
                        background: ${{CONFIG.secondaryColor}};
                    ">
                        <div class="ccgpt-message ccgpt-bot" style="
                            background: white;
                            padding: 12px;
                            border-radius: 8px;
                            margin-bottom: 12px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            color: ${{CONFIG.textColor}};
                        ">
                            ${{CONFIG.welcomeMessage}}
                        </div>
                    </div>
                    
                    <div id="ccgpt-input-container" style="
                        padding: 16px;
                        background: white;
                        border-top: 1px solid #e0e0e0;
                        border-radius: 0 0 12px 12px;
                    ">
                        <div style="display: flex; gap: 8px;">
                            <input id="ccgpt-input" type="text" placeholder="${{CONFIG.placeholder}}" style="
                                flex: 1;
                                padding: 12px;
                                border: 1px solid #ddd;
                                border-radius: 20px;
                                outline: none;
                                font-size: 14px;
                                color: ${{CONFIG.textColor}};
                            ">
                            <button id="ccgpt-send" style="
                                background: ${{CONFIG.primaryColor}};
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
                    background: ${{CONFIG.primaryColor}};
                    color: white;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 8px 20px rgba(37,99,235,0.35);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    overflow: hidden;
                    transition: box-shadow 0.2s ease, transform 0.2s ease;
                " title="Chat">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <rect x="7" y="8" width="10" height="8" rx="2" stroke="white" stroke-width="2"/>
                        <path d="M9 8V6a3 3 0 013-3v0a3 3 0 013 3v2" stroke="white" stroke-width="2" stroke-linecap="round"/>
                        <circle cx="10.5" cy="12" r="1" fill="white"/>
                        <circle cx="13.5" cy="12" r="1" fill="white"/>
                        <path d="M12 16v2" stroke="white" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Apply custom CSS if provided
        if (CONFIG.customCss) {{
            const style = document.createElement('style');
            style.textContent = CONFIG.customCss;
            document.head.appendChild(style);
        }}
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
        
        // Get references
        widget = document.getElementById('ccgpt-widget');
        chatContainer = document.getElementById('ccgpt-chat-container');
        messagesContainer = document.getElementById('ccgpt-messages');
        input = document.getElementById('ccgpt-input');
        sendButton = document.getElementById('ccgpt-send');
        const toggle = document.getElementById('ccgpt-toggle');
        // Shine/dull hover effect
        if (toggle) {{
            toggle.addEventListener('mouseenter', () => {{
                toggle.style.boxShadow = '0 10px 24px rgba(37,99,235,0.5)';
                toggle.style.transform = 'translateY(-1px)';
            }});
            toggle.addEventListener('mouseleave', () => {{
                toggle.style.boxShadow = '0 8px 20px rgba(37,99,235,0.35)';
                toggle.style.transform = 'translateY(0)';
            }});
        }}
    }}
    
    // WebSocket connection
    function connectWebSocket() {{
            try {{
                const base = CONFIG.apiUrl;
                // Robustly derive ws scheme while preserving host (supports https->wss, http->ws)
                const wsBase = base.startsWith('https') ? base.replace('https', 'wss') : base.replace('http', 'ws');
                const wsUrl = `${{wsBase}}/ws/chat/${{sessionId || 'new'}}?client_api_key=${{CONFIG.clientApiKey}}&embed_code_id=${{CONFIG.embedCodeId}}`;
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {{
                console.log('WebSocket connected');
                reconnectAttempts = 0;
            }};
            
            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            }};
            
            ws.onclose = () => {{
                console.log('WebSocket disconnected');
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {{
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, 1000 * reconnectAttempts);
                }}
            }};
            
            ws.onerror = (error) => {{
                console.error('WebSocket error:', error);
            }};
            
        }} catch (error) {{
            console.error('Failed to connect WebSocket:', error);
        }}
    }}
    
    // Handle WebSocket messages
    function handleWebSocketMessage(data) {{
        switch (data.type) {{
            case 'assistant_message_chunk':
                addMessageChunk(data.content);
                break;
            case 'assistant_message_complete':
                finalizeMessage(data.content, data.sources);
                break;
            case 'assistant_typing':
                showTypingIndicator();
                break;
            case 'error':
                hideTypingIndicator();
                addMessage(data.message || 'An error occurred', 'bot');
                break;
        }}
    }}
    
    // Attach event listeners
    function attachEventListeners() {{
        const toggle = document.getElementById('ccgpt-toggle');
        const close = document.getElementById('ccgpt-close');
        
        toggle.addEventListener('click', toggleChat);
        close.addEventListener('click', closeChat);
        sendButton.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') sendMessage();
        }});
    }}
    
    // Toggle chat visibility
    function toggleChat() {{
        isOpen = !isOpen;
        chatContainer.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) {{
            input.focus();
            playSound('open');
        }}
    }}
    
    // Close chat
    function closeChat() {{
        isOpen = false;
        chatContainer.style.display = 'none';
    }}
    
    // Send message
    async function sendMessage() {{
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        if (CONFIG.enableTypingIndicator) {{
            showTypingIndicator();
        }}
        
        // Try WebSocket first, fallback to HTTP
        if (ws && ws.readyState === WebSocket.OPEN) {{
            ws.send(JSON.stringify({{
                type: 'user_message',
                message: message,
                context: {{}}
            }}));
        }} else {{
            // Fallback to HTTP
            try {{
                const response = await fetch(`${{CONFIG.apiUrl}}/api/v1/embed/chat/message`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-Client-API-Key': CONFIG.clientApiKey,
                        'X-Embed-Code-ID': CONFIG.embedCodeId
                    }},
                    body: JSON.stringify({{
                        message: message,
                        session_id: sessionId,
                        // workspace is resolved server-side via API key; do not send from client
                    }})
                }});
                
                if (!response.ok) {{
                    throw new Error('Network response was not ok');
                }}
                
                const data = await response.json();
                
                if (CONFIG.enableTypingIndicator) {{
                    hideTypingIndicator();
                }}
                
                addMessage(data.message.content, 'bot');
                playSound('message');
                
                // Update session ID if provided
                if (data.session_id) {{
                    sessionId = data.session_id;
                    saveSession();
                }}
                
            }} catch (error) {{
                console.error('Chat error:', error);
                if (CONFIG.enableTypingIndicator) {{
                    hideTypingIndicator();
                }}
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }}
        }}
    }}
    
    // Add message to chat
    function addMessage(content, type) {{
        if (messageCount >= CONFIG.maxMessages) {{
            const firstMessage = messagesContainer.firstChild;
            if (firstMessage) {{
                messagesContainer.removeChild(firstMessage);
            }}
        }} else {{
            messageCount++;
        }}
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `ccgpt-message ccgpt-${{type}}`;
        messageDiv.style.cssText = `
            background: ${{type === 'user' ? CONFIG.primaryColor : 'white'}};
            color: ${{type === 'user' ? 'white' : CONFIG.textColor}};
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-left: ${{type === 'user' ? '20px' : '0'}};
            margin-right: ${{type === 'bot' ? '20px' : '0'}};
        `;
        messageDiv.textContent = content;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }}
    
    // Add message chunk (for streaming)
    function addMessageChunk(content) {{
        let lastMessage = messagesContainer.lastElementChild;
        if (!lastMessage || !lastMessage.classList.contains('ccgpt-bot') || lastMessage.id === 'ccgpt-typing') {{
            lastMessage = document.createElement('div');
            lastMessage.className = 'ccgpt-message ccgpt-bot';
            lastMessage.style.cssText = `
                background: white;
                color: ${{CONFIG.textColor}};
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-right: 20px;
            `;
            lastMessage.textContent = '';
            messagesContainer.appendChild(lastMessage);
        }}
        
        lastMessage.textContent += content;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }}
    
    // Finalize streaming message
    function finalizeMessage(content, sources) {{
        hideTypingIndicator();
        if (sources && sources.length > 0) {{
            // Add sources if available
            const sourcesDiv = document.createElement('div');
            sourcesDiv.style.cssText = `
                font-size: 12px;
                color: #666;
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid #eee;
            `;
            sourcesDiv.textContent = `Sources: ${{sources.length}}`;
            messagesContainer.lastElementChild.appendChild(sourcesDiv);
        }}
        playSound('message');
    }}
    
    // Show typing indicator
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
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }}
    
    // Hide typing indicator
    function hideTypingIndicator() {{
        const typing = document.getElementById('ccgpt-typing');
        if (typing) {{
            typing.remove();
        }}
    }}
    
    // Play sound
    function playSound(type) {{
        if (!CONFIG.enableSound) return;
        
        try {{
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(type === 'open' ? 800 : 400, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        }} catch (e) {{
            // Ignore audio errors
        }}
    }}
    
    // Get position CSS
    function getPositionCSS() {{
        const positions = {{
            'bottom-right': 'bottom: 20px; right: 20px;',
            'bottom-left': 'bottom: 20px; left: 20px;',
            'top-right': 'top: 20px; right: 20px;',
            'top-left': 'top: 20px; left: 20px;'
        }};
        return positions[CONFIG.position] || positions['bottom-right'];
    }}
    
    // Get avatar HTML
    function getAvatarHTML() {{
        if (!CONFIG.showAvatar) return '';
        
        if (CONFIG.avatarUrl) {{
            return `<img src="${{CONFIG.avatarUrl}}" style="width: 24px; height: 24px; border-radius: 50%;">`;
        }} else {{
            return '<div style="width: 24px; height: 24px; border-radius: 50%; background: rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 12px;">🤖</div>';
        }}
    }}
    
    // Load session from localStorage
    function loadSession() {{
        try {{
            sessionId = localStorage.getItem('ccgpt_session_id');
        }} catch (e) {{
            // Ignore localStorage errors
        }}
    }}
    
    // Save session to localStorage
    function saveSession() {{
        try {{
            if (sessionId) {{
                localStorage.setItem('ccgpt_session_id', sessionId);
            }}
        }} catch (e) {{
            // Ignore localStorage errors
        }}
    }}
    
    // Public API
    window.CustomerCareGPT = {{
        init: init,
        open: () => {{
            if (!isOpen) toggleChat();
        }},
        close: () => {{
            if (isOpen) closeChat();
        }},
        sendMessage: (message) => {{
            if (input) {{
                input.value = message;
                sendMessage();
            }}
        }},
        getSessionId: () => sessionId,
        isConnected: () => ws && ws.readyState === WebSocket.OPEN
    }};
    
    // Auto-initialize
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', init);
    }} else {{
        init();
    }}
}})();
"""
    
    def _generate_embed_html(self, embed_script: str) -> str:
        """Generate HTML embed code"""
        return f"""
<!-- CustomerCareGPT Widget -->
<script>
{embed_script}
</script>
"""
    
    def get_embed_snippet(self, embed_code: EmbedCode) -> str:
        """Get the HTML snippet for embedding"""
        return f"""
<script src="{settings.API_BASE_URL}/api/v1/embed/widget/{embed_code.id}" 
        data-embed-id="{embed_code.id}" 
        data-api-key="{embed_code.client_api_key}">
</script>
"""