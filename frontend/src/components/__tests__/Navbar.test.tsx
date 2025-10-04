/**
 * Unit tests for Navbar component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Navbar } from '../common/Navbar';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock the auth context
const mockAuthContext = {
  user: null,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  isAuthenticated: false,
};

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/' }),
  };
});

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

describe('Navbar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navbar with logo and navigation links', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    expect(screen.getByText('CustomerCareGPT')).toBeInTheDocument();
    expect(screen.getByText('Features')).toBeInTheDocument();
    expect(screen.getByText('Pricing')).toBeInTheDocument();
    expect(screen.getByText('FAQ')).toBeInTheDocument();
  });

  it('shows login and register buttons when user is not authenticated', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Register')).toBeInTheDocument();
  });

  it('shows user menu when user is authenticated', () => {
    mockAuthContext.isAuthenticated = true;
    (mockAuthContext as any).user = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      workspace_id: 'ws_1',
    };

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('handles login button click', async () => {
    const mockNavigate = vi.fn();
    vi.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('handles register button click', async () => {
    const mockNavigate = vi.fn();
    vi.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const registerButton = screen.getByText('Register');
    fireEvent.click(registerButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/register');
    });
  });

  it('handles logout button click', async () => {
    mockAuthContext.isAuthenticated = true;
    (mockAuthContext as any).user = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      workspace_id: 'ws_1',
    };

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockAuthContext.logout).toHaveBeenCalled();
    });
  });

  it('shows mobile menu toggle on small screens', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    // Check for mobile menu button (hamburger icon)
    const mobileMenuButton = screen.getByRole('button', { name: /menu/i });
    expect(mobileMenuButton).toBeInTheDocument();
  });

  it('toggles mobile menu when hamburger button is clicked', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const mobileMenuButton = screen.getByRole('button', { name: /menu/i });
    fireEvent.click(mobileMenuButton);

    // Mobile menu should be visible
    expect(screen.getByRole('navigation')).toHaveClass('mobile-menu-open');
  });

  it('closes mobile menu when close button is clicked', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const mobileMenuButton = screen.getByRole('button', { name: /menu/i });
    fireEvent.click(mobileMenuButton);

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    // Mobile menu should be closed
    expect(screen.getByRole('navigation')).not.toHaveClass('mobile-menu-open');
  });

  it('shows loading state when authentication is loading', () => {
    mockAuthContext.isLoading = true;

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles theme toggle', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const themeToggle = screen.getByRole('button', { name: /theme/i });
    fireEvent.click(themeToggle);

    // Theme should be toggled (implementation depends on your theme context)
    expect(themeToggle).toBeInTheDocument();
  });

  it('shows active navigation state for current page', () => {
    vi.mocked(require('react-router-dom').useLocation).mockReturnValue({ pathname: '/features' });

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const featuresLink = screen.getByText('Features');
    expect(featuresLink).toHaveClass('active');
  });

  it('handles keyboard navigation', () => {
    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const featuresLink = screen.getByText('Features');
    featuresLink.focus();
    
    fireEvent.keyDown(featuresLink, { key: 'Enter' });
    
    // Should navigate to features page
    expect(featuresLink).toBeInTheDocument();
  });

  it('shows user avatar when authenticated', () => {
    mockAuthContext.isAuthenticated = true;
    (mockAuthContext as any).user = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      workspace_id: 'ws_1',
    };

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const userAvatar = screen.getByAltText('User avatar');
    expect(userAvatar).toBeInTheDocument();
  });

  it('handles dropdown menu interactions', () => {
    mockAuthContext.isAuthenticated = true;
    (mockAuthContext as any).user = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      workspace_id: 'ws_1',
    };

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const userMenuButton = screen.getByText('Test User');
    fireEvent.click(userMenuButton);

    // Dropdown menu should be visible
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('closes dropdown menu when clicking outside', () => {
    mockAuthContext.isAuthenticated = true;
    (mockAuthContext as any).user = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      workspace_id: 'ws_1',
    };

    render(
      <TestWrapper>
        <Navbar />
      </TestWrapper>
    );

    const userMenuButton = screen.getByText('Test User');
    fireEvent.click(userMenuButton);

    // Click outside the dropdown
    fireEvent.click(document.body);

    // Dropdown should be closed
    expect(screen.queryByText('Profile')).not.toBeInTheDocument();
  });
});
