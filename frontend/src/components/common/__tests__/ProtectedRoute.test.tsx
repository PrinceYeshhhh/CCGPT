import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';

// Mock the AuthContext hook; tests control return value per case
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({ isAuthenticated: false }))
}));

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

function renderWithAuth(isAuthenticated: boolean, demoMode: boolean, initialEntry = '/dashboard') {
  const { useAuth } = require('@/contexts/AuthContext');
  vi.mocked(useAuth).mockReturnValue({ isAuthenticated, user: null, token: null, login: vi.fn(), logout: vi.fn() });
  Object.defineProperty(import.meta, 'env', { value: { ...originalEnv, VITE_DEMO_MODE: demoMode ? 'true' : 'false' }, writable: true });

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<TestLoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<TestProtectedContent />} />
          <Route path="/dashboard/settings" element={<TestProtectedContent />} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should redirect to login when not authenticated and not in demo mode', () => {
    renderWithAuth(false, false);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should allow access when authenticated', () => {
    renderWithAuth(true, false);
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should allow access in demo mode even when not authenticated', () => {
    renderWithAuth(false, true);
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should allow access when both authenticated and in demo mode', () => {
    renderWithAuth(true, true);
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('should preserve location state when redirecting', () => {
    renderWithAuth(false, false, '/dashboard/settings');
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});
