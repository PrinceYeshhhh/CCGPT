import React from 'react';
import { render as rtlRender, RenderOptions, cleanup } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { vi, afterEach } from 'vitest';
import { QueryCache } from 'react-query';

// Mock the auth context
const mockAuthContext = {
  user: null,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  isAuthenticated: false,
};

// Mock react-router-dom
const mockNavigate = vi.fn();

// Mock the auth context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: '/' }),
  };
});

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  theme?: 'light' | 'dark';
  authState?: any;
}

// Use a singleton QueryClient to avoid spawning per-test timers
const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      // Prevent background GC timers from keeping Vitest alive
      cacheTime: 0,
      staleTime: Infinity,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
    },
    mutations: { retry: false },
  },
  queryCache: new QueryCache(),
});

// Ensure the query client doesn't leave pending timers/handles between tests
afterEach(() => {
  try {
    testQueryClient.clear();
    testQueryClient.removeQueries();
    testQueryClient.getQueryCache().clear();
  } catch {}
  cleanup();
});

const AllTheProviders = ({ 
  children, 
  theme = 'light', 
  authState = {} 
}: { 
  children: React.ReactNode; 
  theme?: 'light' | 'dark';
  authState?: any;
}) => {
  // Update mock auth context with provided state
  if (authState) {
    Object.assign(mockAuthContext, authState);
  }

  return (
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { theme, authState, ...renderOptions } = options;
  
  return rtlRender(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders theme={theme} authState={authState}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  });
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Helper to update auth state in tests
export const updateAuthState = (newState: any) => {
  Object.assign(mockAuthContext, newState);
};

// Helper to reset auth state
export const resetAuthState = () => {
  Object.assign(mockAuthContext, {
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    isAuthenticated: false,
  });
};

// Export mock navigate for tests
export { mockNavigate };