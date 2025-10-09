import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { api, setAuthToken, getAuthToken } from '../api';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.location
const mockLocation = {
  href: '',
  pathname: '/test',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  value: true,
  writable: true,
});

// Mock environment variables
const originalEnv = import.meta.env;

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    Object.defineProperty(import.meta, 'env', {
      value: { ...originalEnv, VITE_API_BASE_URL: 'https://api.example.com' },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(import.meta, 'env', {
      value: originalEnv,
      writable: true,
    });
  });

  describe('api instance', () => {
    it('should create axios instance with correct configuration', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://api.example.com',
        withCredentials: true,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
    });
  });

  describe('setAuthToken', () => {
    it('should set auth token in localStorage', () => {
      setAuthToken('test-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'test-token');
    });

    it('should remove auth token when null is passed', () => {
      setAuthToken(null);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('getAuthToken', () => {
    it('should get auth token from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      const token = getAuthToken();
      expect(token).toBe('test-token');
      expect(localStorageMock.getItem).toHaveBeenCalledWith('auth_token');
    });

    it('should return null when no token exists', () => {
      localStorageMock.getItem.mockReturnValue(null);
      const token = getAuthToken();
      expect(token).toBeNull();
    });
  });

  describe('request interceptor', () => {
    it('should add CSRF token to headers when available', () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'csrf_token') return 'csrf-token';
        if (key === 'auth_token') return 'auth-token';
        return null;
      });

      const mockConfig = { headers: {} };
      const mockRequest = { ...mockConfig };
      
      // Get the request interceptor
      const requestInterceptor = mockedAxios.create.mock.results[0].value.interceptors.request.use.mock.calls[0][0];
      
      const result = requestInterceptor(mockRequest);
      
      expect(result.headers['X-CSRF-Token']).toBe('csrf-token');
      expect(result.headers.Authorization).toBe('Bearer auth-token');
      expect(result.headers['X-Client-Version']).toBe('1.0.0');
    });

    it('should add auth token to headers when available', () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'auth_token') return 'auth-token';
        return null;
      });

      const mockConfig = { headers: {} };
      const mockRequest = { ...mockConfig };
      
      const requestInterceptor = mockedAxios.create.mock.results[0].value.interceptors.request.use.mock.calls[0][0];
      
      const result = requestInterceptor(mockRequest);
      
      expect(result.headers.Authorization).toBe('Bearer auth-token');
    });

    it('should handle missing headers object', () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'auth_token') return 'auth-token';
        return null;
      });

      const mockRequest = {};
      
      const requestInterceptor = mockedAxios.create.mock.results[0].value.interceptors.request.use.mock.calls[0][0];
      
      const result = requestInterceptor(mockRequest);
      
      expect(result.headers.Authorization).toBe('Bearer auth-token');
    });
  });

  describe('response interceptor', () => {
    it('should store CSRF token from response headers', () => {
      const mockResponse = {
        headers: {
          'x-csrf-token': 'new-csrf-token',
        },
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][0];
      
      const result = responseInterceptor(mockResponse);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('csrf_token', 'new-csrf-token');
      expect(result).toBe(mockResponse);
    });

    it('should handle offline detection', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true });
      
      const mockError = { config: {} };
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });

    it('should retry GET requests on transient errors', async () => {
      const mockConfig = { method: 'get', __retryCount: 0 };
      const mockError = { 
        response: { status: 500 },
        config: mockConfig,
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      // Mock the retry call
      const mockApiCall = vi.fn().mockResolvedValue({ data: 'success' });
      mockedAxios.create.mock.results[0].value = mockApiCall;
      
      const result = responseInterceptor(mockError);
      
      // Should return a promise that resolves after retry
      expect(result).toBeInstanceOf(Promise);
    });

    it('should handle 401 authentication errors', () => {
      const mockError = {
        response: { status: 401, data: { message: 'Unauthorized' } },
        config: {},
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('csrf_token');
      expect(mockLocation.href).toBe('/login');
      expect(result).rejects.toBe(mockError);
    });

    it('should handle 429 rate limiting errors', () => {
      const mockError = {
        response: { 
          status: 429, 
          headers: { 'retry-after': '60' },
          data: { message: 'Rate limited' },
        },
        config: {},
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });

    it('should handle 423 account lockout errors', () => {
      const mockError = {
        response: { status: 423, data: { message: 'Account locked' } },
        config: {},
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });

    it('should handle 402 quota exceeded errors', () => {
      const mockError = {
        response: { status: 402, data: { message: 'Quota exceeded' } },
        config: {},
      };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });

    it('should handle network errors', () => {
      const mockError = { request: {} };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });

    it('should handle other errors', () => {
      const mockError = { message: 'Unknown error' };
      
      const responseInterceptor = mockedAxios.create.mock.results[0].value.interceptors.response.use.mock.calls[0][1];
      
      const result = responseInterceptor(mockError);
      
      expect(result).rejects.toBe(mockError);
    });
  });
});
