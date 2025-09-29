import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api/v1') as string;

console.log('API Configuration:', { 
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


