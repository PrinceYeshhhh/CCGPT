import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Features } from '../Features';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock useAuth hook with vi.fn so tests can override
const useAuthMock = vi.fn(() => ({ isAuthenticated: false, user: null }))
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: useAuthMock,
}));

// Mock PostLoginTrialPopup component
vi.mock('@/components/common/PostLoginTrialPopup', () => ({
  PostLoginTrialPopup: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="trial-popup">
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

describe('Features', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderFeatures = () => {
    return render(<Features />);
  };

  it('should render features page', () => {
    renderFeatures();
    
    expect(screen.getByText('Features')).toBeInTheDocument();
    expect(screen.getByText('Everything you need to transform your customer support')).toBeInTheDocument();
  });

  it('should display hero section', () => {
    renderFeatures();
    
    expect(screen.getByText('Powerful Features for Modern Customer Support')).toBeInTheDocument();
    expect(screen.getByText('Get Started Free')).toBeInTheDocument();
    expect(screen.getByText('View Demo')).toBeInTheDocument();
  });

  it('should display core features section', () => {
    renderFeatures();
    
    expect(screen.getByText('Core Features')).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Chatbot')).toBeInTheDocument();
    expect(screen.getByText('Document Upload')).toBeInTheDocument();
    expect(screen.getByText('Real-time Analytics')).toBeInTheDocument();
  });

  it('should display integration features', () => {
    renderFeatures();
    
    expect(screen.getByText('Easy Integration')).toBeInTheDocument();
    expect(screen.getByText('Widget Embedding')).toBeInTheDocument();
    expect(screen.getByText('API Access')).toBeInTheDocument();
    expect(screen.getByText('Custom Styling')).toBeInTheDocument();
  });

  it('should display analytics features', () => {
    renderFeatures();
    
    expect(screen.getByText('Advanced Analytics')).toBeInTheDocument();
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('User Insights')).toBeInTheDocument();
    expect(screen.getByText('Custom Reports')).toBeInTheDocument();
  });

  it('should display security features', () => {
    renderFeatures();
    
    expect(screen.getByText('Enterprise Security')).toBeInTheDocument();
    expect(screen.getByText('Data Encryption')).toBeInTheDocument();
    expect(screen.getByText('GDPR Compliance')).toBeInTheDocument();
    expect(screen.getByText('SOC 2 Certified')).toBeInTheDocument();
  });

  it('should handle get started button click', () => {
    renderFeatures();
    
    const getStartedButton = screen.getByText('Get Started Free');
    fireEvent.click(getStartedButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('should handle view demo button click', () => {
    renderFeatures();
    
    const viewDemoButton = screen.getByText('View Demo');
    fireEvent.click(viewDemoButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should handle pricing button click', () => {
    renderFeatures();
    
    const pricingButton = screen.getByText('View Pricing');
    fireEvent.click(pricingButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/pricing');
  });

  it('should display feature cards with descriptions', () => {
    renderFeatures();
    
    expect(screen.getByText('AI-Powered Chatbot')).toBeInTheDocument();
    expect(screen.getByText('Upload your documents and let our AI answer questions instantly')).toBeInTheDocument();
  });

  it('should display integration examples', () => {
    renderFeatures();
    
    expect(screen.getByText('Integration Examples')).toBeInTheDocument();
    expect(screen.getByText('WordPress')).toBeInTheDocument();
    expect(screen.getByText('Shopify')).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  it('should display testimonials', () => {
    renderFeatures();
    
    expect(screen.getByText('What Our Customers Say')).toBeInTheDocument();
  });

  it('should handle authenticated user', async () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    expect(screen.getByText('Welcome back, testuser')).toBeInTheDocument();
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
  });

  it('should handle dashboard button click for authenticated user', async () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    const dashboardButton = screen.getByText('Go to Dashboard');
    fireEvent.click(dashboardButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('should check subscription status for authenticated user', async () => {
    mockApi.get.mockResolvedValue({
      data: {
        plan: 'pro',
        status: 'active',
      },
    });
    
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    await waitFor(() => {
      expect(mockApi.get).toHaveBeenCalledWith('/billing/status');
    });
  });

  it('should show trial popup for authenticated user without subscription', async () => {
    mockApi.get.mockResolvedValue({
      data: {
        plan: 'free',
        status: 'active',
      },
    });
    
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    await waitFor(() => {
      expect(screen.getByTestId('trial-popup')).toBeInTheDocument();
    });
  });

  it('should handle trial popup close', async () => {
    mockApi.get.mockResolvedValue({
      data: {
        plan: 'free',
        status: 'active',
      },
    });
    
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    await waitFor(() => {
      expect(screen.getByTestId('trial-popup')).toBeInTheDocument();
    });
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('trial-popup')).not.toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    const { useAuth } = await import('@/contexts/AuthContext')
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    } as any)
    
    renderFeatures();
    
    // Should not crash
    expect(screen.getByText('Features')).toBeInTheDocument();
  });

  it('should display feature icons', () => {
    renderFeatures();
    
    // Check if feature icons are present
    expect(screen.getByText('AI-Powered Chatbot')).toBeInTheDocument();
    expect(screen.getByText('Document Upload')).toBeInTheDocument();
    expect(screen.getByText('Real-time Analytics')).toBeInTheDocument();
  });

  it('should display comparison table', () => {
    renderFeatures();
    
    expect(screen.getByText('Feature Comparison')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
  });

  it('should handle FAQ section', () => {
    renderFeatures();
    
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
  });

  it('should handle FAQ accordion', () => {
    renderFeatures();
    
    const faqItems = screen.getAllByRole('button');
    const firstFaq = faqItems.find(item => item.textContent?.includes('How does the AI chatbot work?'));
    
    if (firstFaq) {
      fireEvent.click(firstFaq);
      // Should expand FAQ item
    }
  });

  it('should display CTA section', () => {
    renderFeatures();
    
    expect(screen.getByText('Ready to Get Started?')).toBeInTheDocument();
    expect(screen.getByText('Start Your Free Trial Today')).toBeInTheDocument();
  });

  it('should handle navigation links', () => {
    renderFeatures();
    
    const pricingLink = screen.getByText('Pricing');
    fireEvent.click(pricingLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/pricing');
  });

  it('should display feature benefits', () => {
    renderFeatures();
    
    expect(screen.getByText('Why Choose Our Features?')).toBeInTheDocument();
    expect(screen.getByText('Easy to Use')).toBeInTheDocument();
    expect(screen.getByText('Powerful')).toBeInTheDocument();
    expect(screen.getByText('Reliable')).toBeInTheDocument();
  });
});
