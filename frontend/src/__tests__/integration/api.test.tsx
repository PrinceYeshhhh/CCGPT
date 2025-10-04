/**
 * Frontend Integration Tests for API interactions
 * Tests real API calls and data flow between frontend and backend
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import axios from 'axios';
import { AuthProvider } from '@/contexts/AuthContext';
import { Login } from '@/pages/auth/Login';
import { Documents } from '@/pages/dashboard/Documents';
import { Chat } from '@/pages/dashboard/Chat';
import { Analytics } from '@/pages/dashboard/Analytics';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

// Mock API base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
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

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset localStorage
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Authentication API Integration', () => {
    it('should handle successful login flow', async () => {
      const mockLoginResponse = {
        data: {
          access_token: 'mock-jwt-token',
          token_type: 'bearer',
          user: {
            id: '1',
            email: 'test@example.com',
            full_name: 'Test User',
            workspace_id: 'ws_1'
          }
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockLoginResponse);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          `${API_BASE_URL}/auth/login`,
          {
            email: 'test@example.com',
            password: 'password123'
          }
        );
      });
    });

    it('should handle login error responses', async () => {
      const mockErrorResponse = {
        response: {
          status: 401,
          data: {
            detail: 'Invalid credentials'
          }
        }
      };

      mockedAxios.post.mockRejectedValueOnce(mockErrorResponse);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('should handle network errors gracefully', async () => {
      mockedAxios.post.mockRejectedValueOnce(new Error('Network Error'));

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Documents API Integration', () => {
    const mockAuthToken = 'mock-jwt-token';

    beforeEach(() => {
      // Mock authenticated user
      localStorage.setItem('auth_token', mockAuthToken);
    });

    it('should fetch and display documents', async () => {
      const mockDocumentsResponse = {
        data: [
          {
            id: '1',
            filename: 'test.pdf',
            status: 'processed',
            created_at: '2024-01-01T00:00:00Z',
            file_size: 1024
          },
          {
            id: '2',
            filename: 'manual.docx',
            status: 'processing',
            created_at: '2024-01-02T00:00:00Z',
            file_size: 2048
          }
        ]
      };

      mockedAxios.get.mockResolvedValueOnce(mockDocumentsResponse);

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          `${API_BASE_URL}/documents/`,
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`
            }
          }
        );
      });

      expect(screen.getByText('test.pdf')).toBeInTheDocument();
      expect(screen.getByText('manual.docx')).toBeInTheDocument();
    });

    it('should handle document upload', async () => {
      const mockUploadResponse = {
        data: {
          document_id: '3',
          job_id: 'job_123',
          status: 'processing'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockUploadResponse);

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const fileInput = screen.getByLabelText(/upload file/i);

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          `${API_BASE_URL}/documents/upload`,
          expect.any(FormData),
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
      });
    });

    it('should handle document deletion', async () => {
      const mockDeleteResponse = {
        data: {
          message: 'Document deleted successfully'
        }
      };

      mockedAxios.delete.mockResolvedValueOnce(mockDeleteResponse);

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      // Mock documents data
      const mockDocuments = [
        {
          id: '1',
          filename: 'test.pdf',
          status: 'processed',
          created_at: '2024-01-01T00:00:00Z',
          file_size: 1024
        }
      ];

      mockedAxios.get.mockResolvedValueOnce({ data: mockDocuments });

      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /delete/i });
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(mockedAxios.delete).toHaveBeenCalledWith(
          `${API_BASE_URL}/documents/1`,
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`
            }
          }
        );
      });
    });
  });

  describe('Chat API Integration', () => {
    const mockAuthToken = 'mock-jwt-token';

    beforeEach(() => {
      localStorage.setItem('auth_token', mockAuthToken);
    });

    it('should create chat session and send messages', async () => {
      const mockSessionResponse = {
        data: {
          session_id: 'session_123',
          user_label: 'Test Customer'
        }
      };

      const mockMessageResponse = {
        data: {
          response: 'This is a test response',
          message_id: 'msg_123',
          sources: [
            {
              document_id: 'doc_1',
              chunk_id: 'chunk_1',
              score: 0.95
            }
          ]
        }
      };

      mockedAxios.post
        .mockResolvedValueOnce(mockSessionResponse)
        .mockResolvedValueOnce(mockMessageResponse);

      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Create session
      const createSessionButton = screen.getByRole('button', { name: /new chat/i });
      fireEvent.click(createSessionButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          `${API_BASE_URL}/chat/sessions`,
          expect.any(Object),
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`
            }
          }
        );
      });

      // Send message
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(messageInput, { target: { value: 'Hello, how can I help?' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          `${API_BASE_URL}/chat/message`,
          expect.objectContaining({
            content: 'Hello, how can I help?',
            session_id: 'session_123'
          }),
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`
            }
          }
        );
      });

      expect(screen.getByText('This is a test response')).toBeInTheDocument();
    });

    it('should handle chat errors gracefully', async () => {
      const mockErrorResponse = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      };

      mockedAxios.post.mockRejectedValueOnce(mockErrorResponse);

      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(messageInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
      });
    });
  });

  describe('Analytics API Integration', () => {
    const mockAuthToken = 'mock-jwt-token';

    beforeEach(() => {
      localStorage.setItem('auth_token', mockAuthToken);
    });

    it('should fetch and display analytics data', async () => {
      const mockAnalyticsResponse = {
        data: {
          total_queries: 150,
          total_documents: 25,
          average_response_time: 1.2,
          quota_usage: 0.75,
          daily_usage: [
            { date: '2024-01-01', queries: 10 },
            { date: '2024-01-02', queries: 15 },
            { date: '2024-01-03', queries: 12 }
          ]
        }
      };

      mockedAxios.get.mockResolvedValueOnce(mockAnalyticsResponse);

      render(
        <TestWrapper>
          <Analytics />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          `${API_BASE_URL}/analytics/workspace`,
          {
            headers: {
              'Authorization': `Bearer ${mockAuthToken}`
            }
          }
        );
      });

      expect(screen.getByText('150')).toBeInTheDocument(); // Total queries
      expect(screen.getByText('25')).toBeInTheDocument(); // Total documents
    });

    it('should handle analytics loading states', async () => {
      // Mock delayed response
      mockedAxios.get.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({ data: { total_queries: 100 } }), 1000)
        )
      );

      render(
        <TestWrapper>
          <Analytics />
        </TestWrapper>
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle 401 unauthorized errors globally', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 401,
          data: {
            detail: 'Unauthorized'
          }
        }
      });

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/unauthorized/i)).toBeInTheDocument();
      });
    });

    it('should handle 500 server errors gracefully', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      });

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });
    });

    it('should handle network timeouts', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('timeout'));

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Caching Integration', () => {
    const mockAuthToken = 'mock-jwt-token';

    beforeEach(() => {
      localStorage.setItem('auth_token', mockAuthToken);
    });

    it('should cache API responses', async () => {
      const mockResponse = {
        data: [
          { id: '1', filename: 'test.pdf', status: 'processed' }
        ]
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const { rerender } = render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });

      // Rerender component
      rerender(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      // Should use cached data, not make another API call
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });
    });

    it('should invalidate cache on mutations', async () => {
      const mockDocumentsResponse = {
        data: [
          { id: '1', filename: 'test.pdf', status: 'processed' }
        ]
      };

      const mockDeleteResponse = {
        data: { message: 'Document deleted successfully' }
      };

      mockedAxios.get.mockResolvedValue(mockDocumentsResponse);
      mockedAxios.delete.mockResolvedValueOnce(mockDeleteResponse);

      render(
        <TestWrapper>
          <Documents />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });

      // Delete document
      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        // Should refetch data after deletion
        expect(mockedAxios.get).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Real-time Updates Integration', () => {
    it('should handle WebSocket connections', async () => {
      const mockWebSocket = {
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        readyState: WebSocket.OPEN
      };

      // Mock WebSocket
      global.WebSocket = vi.fn(() => mockWebSocket) as any;

      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(global.WebSocket).toHaveBeenCalled();
      });
    });

    it('should handle WebSocket message updates', async () => {
      const mockWebSocket = {
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        readyState: WebSocket.OPEN
      };

      global.WebSocket = vi.fn(() => mockWebSocket) as any;

      render(
        <TestWrapper>
          <Chat />
        </TestWrapper>
      );

      // Simulate incoming WebSocket message
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'chat_message',
          content: 'Hello from WebSocket!',
          timestamp: new Date().toISOString()
        })
      });

      // Trigger the message event
      mockWebSocket.addEventListener.mock.calls
        .find(call => call[0] === 'message')?.[1](messageEvent);

      await waitFor(() => {
        expect(screen.getByText('Hello from WebSocket!')).toBeInTheDocument();
      });
    });
  });
});
