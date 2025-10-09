import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock all the lazy-loaded components
vi.mock('@/pages/public/Home', () => ({
  Home: () => <div data-testid="home-page">Home Page</div>,
}));

vi.mock('@/pages/public/Features', () => ({
  Features: () => <div data-testid="features-page">Features Page</div>,
}));

vi.mock('@/pages/public/Pricing', () => ({
  Pricing: () => <div data-testid="pricing-page">Pricing Page</div>,
}));

vi.mock('@/pages/public/FAQ', () => ({
  FAQ: () => <div data-testid="faq-page">FAQ Page</div>,
}));

vi.mock('@/pages/auth/Login', () => ({
  Login: () => <div data-testid="login-page">Login Page</div>,
}));

vi.mock('@/pages/auth/Register', () => ({
  Register: () => <div data-testid="register-page">Register Page</div>,
}));

vi.mock('@/pages/public/UserProfile', () => ({
  UserProfile: () => <div data-testid="user-profile-page">User Profile Page</div>,
}));

vi.mock('@/pages/dashboard/DashboardLayout', () => ({
  DashboardLayout: () => <div data-testid="dashboard-layout">Dashboard Layout</div>,
}));

vi.mock('@/pages/dashboard/Overview', () => ({
  Overview: () => <div data-testid="overview-page">Overview Page</div>,
}));

vi.mock('@/pages/dashboard/Documents', () => ({
  Documents: () => <div data-testid="documents-page">Documents Page</div>,
}));

vi.mock('@/pages/dashboard/Embed', () => ({
  Embed: () => <div data-testid="embed-page">Embed Page</div>,
}));

vi.mock('@/pages/dashboard/Analytics', () => ({
  Analytics: () => <div data-testid="analytics-page">Analytics Page</div>,
}));

vi.mock('@/pages/dashboard/Performance', () => ({
  Performance: () => <div data-testid="performance-page">Performance Page</div>,
}));

vi.mock('@/pages/dashboard/Billing', () => ({
  Billing: () => <div data-testid="billing-page">Billing Page</div>,
}));

vi.mock('@/pages/dashboard/Settings', () => ({
  Settings: () => <div data-testid="settings-page">Settings Page</div>,
}));

// Mock components
vi.mock('@/components/common/Navbar', () => ({
  Navbar: () => <div data-testid="navbar">Navbar</div>,
}));

vi.mock('@/components/common/Footer', () => ({
  Footer: () => <div data-testid="footer">Footer</div>,
}));

vi.mock('@/components/common/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div data-testid="protected-route">{children}</div>,
}));

vi.mock('@/components/common/NotFound', () => ({
  NotFound: () => <div data-testid="not-found">Not Found</div>,
}));

vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="auth-provider">{children}</div>,
}));

vi.mock('@/contexts/ThemeContext', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="theme-provider">{children}</div>,
}));

vi.mock('@/lib/error-monitoring', () => ({
  initErrorMonitoring: vi.fn(),
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div data-testid="error-boundary">{children}</div>,
  ErrorFallback: () => <div data-testid="error-fallback">Error Fallback</div>,
}));

vi.mock('react-query', () => ({
  QueryClient: vi.fn().mockImplementation(() => ({})),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="query-client-provider">{children}</div>,
}));

vi.mock('react-hot-toast', () => ({
  Toaster: () => <div data-testid="toaster">Toaster</div>,
}));

// Mock environment variables
const originalEnv = import.meta.env;

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(import.meta, 'env', {
      value: { ...originalEnv, VITE_DEMO_MODE: 'false' },
      writable: true,
    });
  });

  it('should render without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
  });

  it('should render all providers in correct order', () => {
    render(<App />);
    
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
    expect(screen.getByTestId('query-client-provider')).toBeInTheDocument();
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
  });

  it('should render home page for root route', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });
  });

  it('should render features page for /features route', async () => {
    render(
      <MemoryRouter initialEntries={['/features']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('features-page')).toBeInTheDocument();
    });
  });

  it('should render pricing page for /pricing route', async () => {
    render(
      <MemoryRouter initialEntries={['/pricing']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('pricing-page')).toBeInTheDocument();
    });
  });

  it('should render FAQ page for /faq route', async () => {
    render(
      <MemoryRouter initialEntries={['/faq']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('faq-page')).toBeInTheDocument();
    });
  });

  it('should render login page for /login route', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  it('should render register page for /register route', async () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('register-page')).toBeInTheDocument();
    });
  });

  it('should render user profile page for /profile route', async () => {
    render(
      <MemoryRouter initialEntries={['/profile']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-profile-page')).toBeInTheDocument();
    });
  });

  it('should render dashboard layout for /dashboard route', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('dashboard-layout')).toBeInTheDocument();
    });
  });

  it('should render not found page for unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('not-found')).toBeInTheDocument();
    });
  });

  it('should render loading fallback during suspense', () => {
    render(<App />);
    
    // The loading fallback should be present initially
    expect(screen.getByText('Loading CustomerCareGPT...')).toBeInTheDocument();
  });

  it('should render toaster component', () => {
    render(<App />);
    expect(screen.getByTestId('toaster')).toBeInTheDocument();
  });

  it('should not render performance monitor in production', () => {
    Object.defineProperty(process, 'env', {
      value: { ...process.env, NODE_ENV: 'production' },
      writable: true,
    });

    render(<App />);
    
    expect(screen.queryByTestId('performance-monitor')).not.toBeInTheDocument();
  });
});
