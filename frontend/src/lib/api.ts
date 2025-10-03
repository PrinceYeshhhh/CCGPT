import axios from 'axios';
import toast from 'react-hot-toast';

// Prefer relative proxy in Vite dev to avoid loopback/CORS issues
const isDev = typeof window !== 'undefined' && window.location && window.location.port === '5173';
let API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api/v1') as string;
if (isDev) {
  API_BASE_URL = '/api/v1';
}

console.log('API Configuration:', {
  isDev,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_API_URL: import.meta.env.VITE_API_URL,
  API_BASE_URL
});

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

// Request interceptor with enhanced security
api.interceptors.request.use(
  (config) => {
    // Add CSRF token if available
    const csrfToken = localStorage.getItem('csrf_token');
    if (csrfToken) {
      config.headers = config.headers ?? {};
      config.headers['X-CSRF-Token'] = csrfToken;
    }
    
    // Add auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add client version for security tracking
    config.headers = config.headers ?? {};
    config.headers['X-Client-Version'] = '1.0.0';
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor with enhanced error handling
api.interceptors.response.use(
  (response) => {
    // Store CSRF token if provided
    const csrfToken = response.headers['x-csrf-token'];
    if (csrfToken) {
      localStorage.setItem('csrf_token', csrfToken);
    }
    
    return response;
  },
  (error) => {
    // Offline handling
    try {
      if (typeof navigator !== 'undefined' && navigator && (navigator as any).onLine === false) {
        toast.error('You appear to be offline. Please check your connection.');
        return Promise.reject(error);
      }
    } catch {}

    // Lightweight retry for idempotent GETs and transient network/server errors
    const config = error.config || {};
    const method = (config.method || '').toLowerCase();
    const shouldRetry = method === 'get' || method === 'head';
    const status = error?.response?.status;
    const transient = !status || (status >= 500 && status < 600) || status === 429;
    const maxRetries = 3;
    config.__retryCount = config.__retryCount || 0;
    if (shouldRetry && transient && config.__retryCount < maxRetries) {
      config.__retryCount += 1;
      const backoff = Math.min(1000 * Math.pow(2, config.__retryCount - 1), 4000);
      return new Promise((resolve) => setTimeout(resolve, backoff)).then(() => api(config));
    }

    // Handle different types of errors
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      
      // Handle authentication errors
      if (status === 401) {
        // Clear stored tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('csrf_token');
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        toast.error('Session expired. Please log in again.');
        return Promise.reject(error);
      }
      
      // Handle rate limiting
      if (status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        toast.error(`Rate limit exceeded. Please try again in ${retryAfter || 'a few'} seconds.`);
        return Promise.reject(error);
      }
      
      // Handle account lockout
      if (status === 423) {
        toast.error('Account temporarily locked due to multiple failed attempts.');
        return Promise.reject(error);
      }
      
      // Handle quota exceeded
      if (status === 402) {
        toast.error('Quota exceeded. Please upgrade your plan.');
        return Promise.reject(error);
      }
      
      // Show user-friendly error messages
      const message = data?.detail || data?.message || error.message || 'Request failed';
      toast.error(typeof message === 'string' ? message : 'Request failed');
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection and try again.');
    } else {
      // Other error
      toast.error('An unexpected error occurred.');
    }
    
    return Promise.reject(error);
  }
);

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}


