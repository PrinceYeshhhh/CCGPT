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
  login: (token: string, user?: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [user, setUser] = useState<AuthUser | null>(null);

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
    setToken(newToken);
    if (newUser) setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(token),
    login,
    logout,
  }), [user, token, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


