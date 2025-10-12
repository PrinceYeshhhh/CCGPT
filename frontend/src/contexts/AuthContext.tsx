import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { setAuthToken, getAuthToken } from '@/lib/api';

interface AuthUser {
  id?: string;
  username?: string;
  email?: string;
  full_name?: string;
  profile_picture_url?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (token: string, user?: AuthUser) => void;
  logout: () => void;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // console.log('AuthProvider rendering', { token, user }); // Disabled for performance

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  useEffect(() => {
    const isDemo = import.meta.env.VITE_DEMO_MODE === 'true';
    if (isDemo && !token) {
      setToken('demo-token');
      setUser({ username: 'Demo User', email: 'demo@example.com' });
    }
  }, [token]);

  const login = useCallback((newToken: string, newUser?: AuthUser) => {
    try {
      setIsLoading(true);
      setError(null);
      setToken(newToken);
      if (newUser) setUser(newUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    try {
      setIsLoading(true);
      setError(null);
      setToken(null);
      setUser(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else if (response.status === 401) {
        // Try to refresh token first
        try {
          const refreshResponse = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              refresh_token: localStorage.getItem('refresh_token')
            }),
          });
          
          if (refreshResponse.ok) {
            const tokenData = await refreshResponse.json();
            setToken(tokenData.access_token);
            if (tokenData.refresh_token) {
              localStorage.setItem('refresh_token', tokenData.refresh_token);
            }
            // Retry the original request
            return refreshUser();
          } else {
            // Refresh failed, logout
            logout();
          }
        } catch (refreshErr) {
          console.error('Token refresh failed:', refreshErr);
          logout();
        }
      } else {
        throw new Error('Failed to refresh user data');
      }
    } catch (err) {
      console.error('Failed to refresh user:', err);
      setError('Failed to refresh user data');
    } finally {
      setIsLoading(false);
    }
  }, [token, logout]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(token),
    isLoading,
    error,
    login,
    logout,
    clearError,
    refreshUser,
  }), [user, token, isLoading, error, login, logout, clearError, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


