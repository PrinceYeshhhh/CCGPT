import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { X, MessageCircle, Send, Bot } from 'lucide-react';

interface WidgetPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  config: {
    title: string;
    welcome_message: string;
    placeholder: string;
    primary_color: string;
    secondary_color: string;
    text_color: string;
    position: string;
    show_avatar: boolean;
    avatar_url?: string;
    enable_sound: boolean;
    enable_typing_indicator: boolean;
    enable_websocket: boolean;
    theme: string;
    custom_css?: string;
    max_messages: number;
  };
}

export function WidgetPreview({ isOpen, onClose, config }: WidgetPreviewProps) {
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{id: number; text: string; sender: 'user' | 'bot'; timestamp: Date}>>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Add welcome message
      setMessages([{
        id: 1,
        text: config.welcome_message,
        sender: 'bot',
        timestamp: new Date()
      }]);
    }
  }, [isOpen, config.welcome_message]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user' as const,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response
    if (config.enable_typing_indicator) {
      setIsTyping(true);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }

    typingTimeoutRef.current = window.setTimeout(() => {
      setIsTyping(false);
      const botMessage = {
        id: messages.length + 2,
        text: "Thank you for your message! This is a preview of how the chatbot will respond. In the actual implementation, this would be connected to your AI system.",
        sender: 'bot' as const,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      typingTimeoutRef.current = null;
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = null;
      }
    };
  }, []);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[600px] p-0">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle className="flex items-center justify-between">
            <span>Widget Preview</span>
            <Button variant="ghost" size="sm" onClick={onClose} data-testid="dialog-close-button">
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
          <DialogDescription>
            This is how your chat widget will appear on your website. Click the chat bubble to interact with it.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 relative bg-gray-50 dark:bg-gray-900 rounded-lg mx-6 mb-6 overflow-hidden">
          {/* Mock Website Content */}
          <div className="p-8">
            <h1 className="text-2xl font-bold mb-4">Your Website</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              This is a preview of how your chat widget will appear on your website. 
              The widget will be positioned in the {config.position} corner.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <h3 className="font-semibold mb-2">Feature 1</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Description of your first feature.</p>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                <h3 className="font-semibold mb-2">Feature 2</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Description of your second feature.</p>
              </div>
            </div>
          </div>

          {/* Chat Widget */}
          <div 
            className={`fixed ${config.position === 'bottom-right' ? 'bottom-4 right-4' : 'bottom-4 left-4'} z-50`}
            style={{ 
              '--primary-color': config.primary_color,
              '--secondary-color': config.secondary_color,
              '--text-color': config.text_color
            } as React.CSSProperties}
          >
            {!isWidgetOpen ? (
              // Chat Bubble
              <button
                onClick={() => setIsWidgetOpen(true)}
                className="w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-white hover:scale-105 transition-transform"
                style={{ backgroundColor: config.primary_color }}
                data-testid="chat-bubble-button"
                aria-label="Open chat widget"
              >
                <MessageCircle className="h-6 w-6" />
              </button>
            ) : (
              // Chat Window
              <div 
                className="w-80 h-96 rounded-lg shadow-xl flex flex-col"
                style={{ 
                  backgroundColor: config.secondary_color,
                  color: config.text_color
                }}
              >
                {/* Header */}
                <div 
                  className="p-4 rounded-t-lg flex items-center justify-between"
                  style={{ backgroundColor: config.primary_color, color: 'white' }}
                >
                  <div className="flex items-center space-x-2">
                    {config.show_avatar && (
                      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                        {config.avatar_url ? (
                          <img 
                            src={config.avatar_url} 
                            alt="Bot" 
                            className="w-8 h-8 rounded-full object-cover"
                          />
                        ) : (
                          <Bot className="h-4 w-4" />
                        )}
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-sm">{config.title}</h3>
                      <p className="text-xs opacity-90">Online</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsWidgetOpen(false)}
                    className="text-white/80 hover:text-white"
                    data-testid="chat-window-close-button"
                    aria-label="Close chat widget"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Messages */}
                <div className="flex-1 p-4 overflow-y-auto space-y-3">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                          message.sender === 'user'
                            ? 'text-white'
                            : 'bg-white/10 text-current'
                        }`}
                        style={{
                          backgroundColor: message.sender === 'user' ? config.primary_color : undefined
                        }}
                      >
                        {message.text}
                      </div>
                    </div>
                  ))}
                  
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-white/10 px-3 py-2 rounded-lg text-sm">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input */}
                <div className="p-4 border-t border-white/10">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={config.placeholder}
                      className="flex-1 px-3 py-2 rounded-lg text-sm bg-white/10 border-0 focus:ring-2 focus:ring-white/20 focus:outline-none"
                      style={{ color: config.text_color }}
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim()}
                      className="p-2 rounded-lg text-white disabled:opacity-50 hover:bg-white/10 transition-colors"
                      style={{ backgroundColor: config.primary_color }}
                      data-testid="send-message-button"
                      aria-label="Send message"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
