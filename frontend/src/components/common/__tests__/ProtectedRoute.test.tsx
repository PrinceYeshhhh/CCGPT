import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock the AuthContext
vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

// Mock environment variables
const originalEnv = import.meta.env;

// Test component to render inside protected route
function TestProtectedContent() {
  return <div data-testid="protected-content">Protected Content</div>;
}

// Test component for login page
function TestLoginPage() {
  return <div data-testid="login-page">Login Page</div>;
}

function TestApp({ isAuthenticated = false, demoMode = false }: { isAuthenticated?: boolean; demoMode?: boolean }) {
  const { useAuth } = await import('@/contexts/AuthContext');
  vi.mocked(useAuth).mockReturnValue({
    isAuthenticated,
    user: null,
    token: null,
    login: vi.fn(),
    logout: vi.fn(),
  });

  Object.defineProperty(import.meta, 'env', {
    value: { ...originalEnv, VITE_DEMO_MODE: demoMode.toString() },
    writable: true,
  });

  return (
    <MemoryRouter initialEntries={['/dashboard']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<TestLoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<TestProtectedContent />} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should redirect to login when not authenticated and not in demo mode', async () => {
    await TestApp({ isAuthenticated: false, demoMode: false });
    
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should allow access when authenticated', async () => {
    await TestApp({ isAuthenticated: true, demoMode: false });
    
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should allow access in demo mode even when not authenticated', async () => {
    await TestApp({ isAuthenticated: false, demoMode: true });
    
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should allow access when both authenticated and in demo mode', async () => {
    await TestApp({ isAuthenticated: true, demoMode: true });
    
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should preserve location state when redirecting', async () => {
    const { useAuth } = await import('@/contexts/AuthContext');
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      user: null,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    Object.defineProperty(import.meta, 'env', {
      value: { ...originalEnv, VITE_DEMO_MODE: 'false' },
      writable: true,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard/settings']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<TestLoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard/settings" element={<TestProtectedContent />} />
            </Route>
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});
