/**
 * CustomerCareGPT Embeddable Chat Widget
 * Version: 1.0.0
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    apiUrl: 'https://customercaregpt-backend-xxxxx-uc.a.run.app',
    codeId: null,
    title: 'Customer Support',
    placeholder: 'Ask me anything...',
    primaryColor: '#007bff',
    position: 'bottom-right',
    showAvatar: true,
    avatarUrl: '',
    welcomeMessage: 'Hello! How can I help you today?',
    maxMessages: 50,
    enableSound: true,
    enableTypingIndicator: true,
    zIndex: 10000
  };

  // State
  let isOpen = false;
  let messageCount = 0;
  let sessionId = null;
  let widget = null;
  let chatContainer = null;
  let messagesContainer = null;
  let input = null;
  let sendButton = null;

  // Initialize widget
  function init(config) {
    CONFIG.codeId = config.codeId;
    Object.assign(CONFIG, config);
    
    createWidget();
    attachEventListeners();
    loadSession();
  }

  // Create widget HTML
  function createWidget() {
    const widgetHTML = `
      <div id="ccgpt-widget" style="
        position: fixed;
        ${getPositionCSS()}
        z-index: ${CONFIG.zIndex};
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
            background: ${CONFIG.primaryColor};
            color: white;
            padding: 16px;
            border-radius: 12px 12px 0 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
          ">
            <div style="display: flex; align-items: center;">
              ${getAvatarHTML()}
              <span style="margin-left: 8px; font-weight: 600;">${CONFIG.title}</span>
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
              ${CONFIG.welcomeMessage}
            </div>
          </div>
          
          <div id="ccgpt-input-container" style="
            padding: 16px;
            background: white;
            border-top: 1px solid #e0e0e0;
            border-radius: 0 0 12px 12px;
          ">
            <div style="display: flex; gap: 8px;">
              <input id="ccgpt-input" type="text" placeholder="${CONFIG.placeholder}" style="
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
                font-size: 14px;
              ">
              <button id="ccgpt-send" style="
                background: ${CONFIG.primaryColor};
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
          background: ${CONFIG.primaryColor};
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

    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    
    // Get references
    widget = document.getElementById('ccgpt-widget');
    chatContainer = document.getElementById('ccgpt-chat-container');
    messagesContainer = document.getElementById('ccgpt-messages');
    input = document.getElementById('ccgpt-input');
    sendButton = document.getElementById('ccgpt-send');
  }

  // Attach event listeners
  function attachEventListeners() {
    const toggle = document.getElementById('ccgpt-toggle');
    const close = document.getElementById('ccgpt-close');

    toggle.addEventListener('click', toggleChat);
    close.addEventListener('click', closeChat);
    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  }

  // Toggle chat visibility
  function toggleChat() {
    isOpen = !isOpen;
    chatContainer.style.display = isOpen ? 'flex' : 'none';
    if (isOpen) {
      input.focus();
      playSound('open');
    }
  }

  // Close chat
  function closeChat() {
    isOpen = false;
    chatContainer.style.display = 'none';
  }

  // Send message
  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    if (CONFIG.enableTypingIndicator) {
      showTypingIndicator();
    }

    try {
      const response = await fetch(`${CONFIG.apiUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          code_id: CONFIG.codeId
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      if (CONFIG.enableTypingIndicator) {
        hideTypingIndicator();
      }
      
      addMessage(data.message.content, 'bot');
      playSound('message');
      
      // Update session ID if provided
      if (data.session_id) {
        sessionId = data.session_id;
        saveSession();
      }

    } catch (error) {
      console.error('Chat error:', error);
      if (CONFIG.enableTypingIndicator) {
        hideTypingIndicator();
      }
      addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
  }

  // Add message to chat
  function addMessage(content, type) {
    if (messageCount >= CONFIG.maxMessages) {
      const firstMessage = messagesContainer.firstChild;
      if (firstMessage) {
        messagesContainer.removeChild(firstMessage);
      }
    } else {
      messageCount++;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `ccgpt-message ccgpt-${type}`;
    messageDiv.style.cssText = `
      background: ${type === 'user' ? CONFIG.primaryColor : 'white'};
      color: ${type === 'user' ? 'white' : 'black'};
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-left: ${type === 'user' ? '20px' : '0'};
      margin-right: ${type === 'bot' ? '20px' : '0'};
    `;
    messageDiv.textContent = content;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Show typing indicator
  function showTypingIndicator() {
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
  }

  // Hide typing indicator
  function hideTypingIndicator() {
    const typing = document.getElementById('ccgpt-typing');
    if (typing) {
      typing.remove();
    }
  }

  // Play sound
  function playSound(type) {
    if (!CONFIG.enableSound) return;
    
    // Simple beep sound using Web Audio API
    try {
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
    } catch (e) {
      // Ignore audio errors
    }
  }

  // Get position CSS
  function getPositionCSS() {
    const positions = {
      'bottom-right': 'bottom: 20px; right: 20px;',
      'bottom-left': 'bottom: 20px; left: 20px;',
      'top-right': 'top: 20px; right: 20px;',
      'top-left': 'top: 20px; left: 20px;'
    };
    return positions[CONFIG.position] || positions['bottom-right'];
  }

  // Get avatar HTML
  function getAvatarHTML() {
    if (!CONFIG.showAvatar) return '';
    
    if (CONFIG.avatarUrl) {
      return `<img src="${CONFIG.avatarUrl}" style="width: 24px; height: 24px; border-radius: 50%;">`;
    } else {
      return '<div style="width: 24px; height: 24px; border-radius: 50%; background: rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 12px;">🤖</div>';
    }
  }

  // Load session from localStorage
  function loadSession() {
    try {
      sessionId = localStorage.getItem('ccgpt_session_id');
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  // Save session to localStorage
  function saveSession() {
    try {
      if (sessionId) {
        localStorage.setItem('ccgpt_session_id', sessionId);
      }
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  // Public API
  window.CustomerCareGPT = {
    init: init,
    open: () => {
      if (!isOpen) toggleChat();
    },
    close: () => {
      if (isOpen) closeChat();
    },
    sendMessage: (message) => {
      if (input) {
        input.value = message;
        sendMessage();
      }
    }
  };

  // Auto-initialize if config is provided
  if (window.CustomerCareGPTConfig) {
    init(window.CustomerCareGPTConfig);
  }

})();
