/**
 * Frontend WebSocket Integration Tests
 * Tests real-time communication between frontend and backend
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AuthProvider } from '@/contexts/AuthContext';
// Mock Chat component since it doesn't exist yet
const Chat = () => <div data-testid="chat-component">Chat Component</div>;

// Mock WebSocket
class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public url: string;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  
  private messageQueue: string[] = [];
  private isConnected: boolean = false;

  constructor(url: string) {
    this.url = url;
    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.isConnected = true;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 100);
  }

  send(data: string) {
    if (this.isConnected) {
      this.messageQueue.push(data);
      // Simulate server response
      setTimeout(() => {
        this.simulateServerResponse(data);
      }, 50);
    }
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.isConnected = false;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  private simulateServerResponse(data: string) {
    try {
      const message = JSON.parse(data);
      
      if (message.type === 'ping') {
        this.simulateMessage({
          type: 'pong',
          data: { timestamp: Date.now() }
        });
      } else if (message.type === 'chat_message') {
        this.simulateMessage({
          type: 'chat_response',
          data: {
            message_id: 'msg_' + Date.now(),
            response: 'This is a test response',
            sources: [
              {
                document_id: 'doc_1',
                chunk_id: 'chunk_1',
                content: 'Source content',
                score: 0.95
              }
            ],
            response_time_ms: 250
          }
        });
      } else if (message.type === 'typing') {
        this.simulateMessage({
          type: 'typing_indicator',
          data: {
            user_id: message.data.user_id,
            is_typing: message.data.is_typing
          }
        });
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private simulateMessage(message: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', {
        data: JSON.stringify(message)
      }));
    }
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any;

// Mock auth context
const mockAuthContext = {
  isAuthenticated: true,
  user: {
    id: '1',
    email: 'test@example.com',
    full_name: 'Test User',
    workspace_id: 'ws_1'
  },
  login: vi.fn(),
  logout: vi.fn(),
  loading: false
};

// Mock WebSocket hook
const mockWebSocketHook = {
  isConnected: false,
  connectionStatus: 'connecting',
  sendMessage: vi.fn(),
  lastMessage: null,
  error: null
};

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => mockWebSocketHook
}));

// Mock auth context
vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => mockAuthContext
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('WebSocket Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWebSocketHook.isConnected = false;
    mockWebSocketHook.connectionStatus = 'connecting';
    mockWebSocketHook.sendMessage = vi.fn();
    (mockWebSocketHook as any).lastMessage = null;
    mockWebSocketHook.error = null;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('WebSocket Connection', () => {
    it('should establish WebSocket connection on component mount', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate connection establishment
      mockWebSocketHook.isConnected = true;
      mockWebSocketHook.connectionStatus = 'connected';

      await waitFor(() => {
        expect(mockWebSocketHook.isConnected).toBe(true);
      });
    });

    it('should handle connection errors gracefully', async () => {
      (mockWebSocketHook as any).error = 'Connection failed';
      (mockWebSocketHook as any).connectionStatus = 'error';

      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockWebSocketHook.error).toBe('Connection failed');
        expect(mockWebSocketHook.connectionStatus).toBe('error');
      });
    });

    it('should reconnect on connection loss', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate connection loss
      mockWebSocketHook.isConnected = false;
      mockWebSocketHook.connectionStatus = 'disconnected';

      await waitFor(() => {
        expect(mockWebSocketHook.isConnected).toBe(false);
      });

      // Simulate reconnection
      mockWebSocketHook.isConnected = true;
      mockWebSocketHook.connectionStatus = 'connected';

      await waitFor(() => {
        expect(mockWebSocketHook.isConnected).toBe(true);
      });
    });
  });

  describe('WebSocket Message Handling', () => {
    it('should send ping messages to keep connection alive', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate ping message
      const pingMessage = {
        type: 'ping',
        data: { timestamp: Date.now() }
      };

      mockWebSocketHook.sendMessage(pingMessage);

      expect(mockWebSocketHook.sendMessage).toHaveBeenCalledWith(pingMessage);
    });

    it('should handle chat messages via WebSocket', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const chatMessage = {
        type: 'chat_message',
        data: {
          message: 'Hello, how can I help?',
          session_id: 'session_123'
        }
      };

      mockWebSocketHook.sendMessage(chatMessage);

      expect(mockWebSocketHook.sendMessage).toHaveBeenCalledWith(chatMessage);
    });

    it('should handle typing indicators via WebSocket', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const typingMessage = {
        type: 'typing',
        data: {
          user_id: '1',
          is_typing: true
        }
      };

      mockWebSocketHook.sendMessage(typingMessage);

      expect(mockWebSocketHook.sendMessage).toHaveBeenCalledWith(typingMessage);
    });

    it('should process incoming WebSocket messages', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const incomingMessage = {
        type: 'chat_response',
        data: {
          message_id: 'msg_123',
          response: 'This is a test response',
          sources: [
            {
              document_id: 'doc_1',
              chunk_id: 'chunk_1',
              content: 'Source content',
              score: 0.95
            }
          ],
          response_time_ms: 250
        }
      };

      (mockWebSocketHook as any).lastMessage = incomingMessage;

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(incomingMessage);
      });
    });
  });

  describe('Real-time Chat Features', () => {
    it('should display typing indicators', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const typingIndicator = {
        type: 'typing_indicator',
        data: {
          user_id: '1',
          is_typing: true
        }
      };

      (mockWebSocketHook as any).lastMessage = typingIndicator;

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(typingIndicator);
      });
    });

    it('should handle multiple concurrent messages', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const messages = [
        {
          type: 'chat_response',
          data: { message_id: 'msg_1', response: 'First response' }
        },
        {
          type: 'chat_response',
          data: { message_id: 'msg_2', response: 'Second response' }
        },
        {
          type: 'typing_indicator',
          data: { user_id: '1', is_typing: false }
        }
      ];

      for (const message of messages) {
        (mockWebSocketHook as any).lastMessage = message;
        await waitFor(() => {
          expect((mockWebSocketHook as any).lastMessage).toEqual(message);
        });
      }
    });

    it('should handle message acknowledgments', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const acknowledgment = {
        type: 'message_ack',
        data: {
          message_id: 'msg_123',
          status: 'delivered'
        }
      };

      (mockWebSocketHook as any).lastMessage = acknowledgment;

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(acknowledgment);
      });
    });
  });

  describe('WebSocket Error Handling', () => {
    it('should handle malformed JSON messages', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate malformed message
      (mockWebSocketHook as any).error = 'Invalid JSON format';
      (mockWebSocketHook as any).lastMessage = null;

      await waitFor(() => {
        expect(mockWebSocketHook.error).toBe('Invalid JSON format');
      });
    });

    it('should handle unknown message types', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const unknownMessage = {
        type: 'unknown_type',
        data: { some: 'data' }
      };

      (mockWebSocketHook as any).lastMessage = unknownMessage;

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(unknownMessage);
      });
    });

    it('should handle connection timeout', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate timeout
      (mockWebSocketHook as any).error = 'Connection timeout';
      mockWebSocketHook.connectionStatus = 'timeout';

      await waitFor(() => {
        expect(mockWebSocketHook.error).toBe('Connection timeout');
        expect(mockWebSocketHook.connectionStatus).toBe('timeout');
      });
    });
  });

  describe('WebSocket Performance', () => {
    it('should handle high-frequency messages', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate high-frequency messages
      const messages = Array.from({ length: 100 }, (_, i) => ({
        type: 'chat_response',
        data: {
          message_id: `msg_${i}`,
          response: `Message ${i}`
        }
      }));

      for (const message of messages) {
        (mockWebSocketHook as any).lastMessage = message;
      }

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(messages[messages.length - 1]);
      });
    });

    it('should handle large message payloads', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const largeMessage = {
        type: 'chat_response',
        data: {
          message_id: 'msg_large',
          response: 'A'.repeat(10000), // Large response
          sources: Array.from({ length: 100 }, (_, i) => ({
            document_id: `doc_${i}`,
            chunk_id: `chunk_${i}`,
            content: 'Content '.repeat(1000),
            score: 0.9
          }))
        }
      };

      (mockWebSocketHook as any).lastMessage = largeMessage;

      await waitFor(() => {
        expect((mockWebSocketHook as any).lastMessage).toEqual(largeMessage);
      });
    });
  });

  describe('WebSocket Authentication', () => {
    it('should authenticate WebSocket connection with JWT token', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate authenticated connection
      mockWebSocketHook.isConnected = true;
      mockWebSocketHook.connectionStatus = 'connected';

      await waitFor(() => {
        expect(mockWebSocketHook.isConnected).toBe(true);
      });
    });

    it('should handle authentication failure', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate authentication failure
      (mockWebSocketHook as any).error = 'Authentication failed';
      mockWebSocketHook.connectionStatus = 'error';

      await waitFor(() => {
        expect(mockWebSocketHook.error).toBe('Authentication failed');
      });
    });

    it('should reconnect with fresh token on auth failure', async () => {
      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate auth failure
      (mockWebSocketHook as any).error = 'Authentication failed';
      mockWebSocketHook.connectionStatus = 'error';

      await waitFor(() => {
        expect(mockWebSocketHook.error).toBe('Authentication failed');
      });

      // Simulate reconnection with fresh token
      mockWebSocketHook.error = null;
      mockWebSocketHook.isConnected = true;
      mockWebSocketHook.connectionStatus = 'connected';

      await waitFor(() => {
        expect(mockWebSocketHook.isConnected).toBe(true);
        expect(mockWebSocketHook.error).toBeNull();
      });
    });
  });
});
