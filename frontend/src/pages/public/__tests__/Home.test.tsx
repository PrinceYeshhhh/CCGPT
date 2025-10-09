import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Home } from '../Home';
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

// Mock useAuth hook
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
  }),
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

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderHome = () => {
    return render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );
  };

  it('should render home page', () => {
    renderHome();
    
    expect(screen.getByText('CustomerCareGPT')).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Customer Support')).toBeInTheDocument();
  });

  it('should display hero section', () => {
    renderHome();
    
    expect(screen.getByText('Transform Your Customer Support with AI')).toBeInTheDocument();
    expect(screen.getByText('Get Started Free')).toBeInTheDocument();
    expect(screen.getByText('View Demo')).toBeInTheDocument();
  });

  it('should display features section', () => {
    renderHome();
    
    expect(screen.getByText('Why Choose CustomerCareGPT?')).toBeInTheDocument();
    expect(screen.getByText('AI-Powered Responses')).toBeInTheDocument();
    expect(screen.getByText('Easy Integration')).toBeInTheDocument();
    expect(screen.getByText('Real-time Analytics')).toBeInTheDocument();
  });

  it('should display pricing section', () => {
    renderHome();
    
    expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
  });

  it('should handle get started button click', () => {
    renderHome();
    
    const getStartedButton = screen.getByText('Get Started Free');
    fireEvent.click(getStartedButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('should handle view demo button click', () => {
    renderHome();
    
    const viewDemoButton = screen.getByText('View Demo');
    fireEvent.click(viewDemoButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should handle pricing button clicks', () => {
    renderHome();
    
    const pricingButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(pricingButtons[0]);
    
    expect(mockNavigate).toHaveBeenCalledWith('/pricing');
  });

  it('should display testimonials section', () => {
    renderHome();
    
    expect(screen.getByText('What Our Customers Say')).toBeInTheDocument();
  });

  it('should display FAQ section', () => {
    renderHome();
    
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
  });

  it('should handle FAQ accordion', () => {
    renderHome();
    
    const faqItems = screen.getAllByRole('button');
    const firstFaq = faqItems.find(item => item.textContent?.includes('What is CustomerCareGPT?'));
    
    if (firstFaq) {
      fireEvent.click(firstFaq);
      // Should expand FAQ item
    }
  });

  it('should display footer', () => {
    renderHome();
    
    expect(screen.getByText('CustomerCareGPT')).toBeInTheDocument();
    expect(screen.getByText('© 2024 CustomerCareGPT. All rights reserved.')).toBeInTheDocument();
  });

  it('should handle authenticated user', () => {
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
    expect(screen.getByText('Welcome back, testuser')).toBeInTheDocument();
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
  });

  it('should handle dashboard button click for authenticated user', () => {
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
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
    
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
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
    
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
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
    
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
    await waitFor(() => {
      expect(screen.getByTestId('trial-popup')).toBeInTheDocument();
    });
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('trial-popup')).not.toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
    // Should not crash
    expect(screen.getByText('CustomerCareGPT')).toBeInTheDocument();
  });

  it('should display loading state', () => {
    vi.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { username: 'testuser', email: 'test@example.com' },
    });
    
    renderHome();
    
    // Should show loading initially
    expect(screen.getByText('CustomerCareGPT')).toBeInTheDocument();
  });

  it('should display feature cards', () => {
    renderHome();
    
    expect(screen.getByText('AI-Powered Responses')).toBeInTheDocument();
    expect(screen.getByText('Easy Integration')).toBeInTheDocument();
    expect(screen.getByText('Real-time Analytics')).toBeInTheDocument();
    expect(screen.getByText('24/7 Support')).toBeInTheDocument();
  });

  it('should display pricing cards', () => {
    renderHome();
    
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('$0')).toBeInTheDocument();
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('$20')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.getByText('$50')).toBeInTheDocument();
  });

  it('should handle navigation links', () => {
    renderHome();
    
    const featuresLink = screen.getByText('Features');
    fireEvent.click(featuresLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/features');
  });

  it('should display social proof', () => {
    renderHome();
    
    expect(screen.getByText('Trusted by 1000+ companies')).toBeInTheDocument();
  });

  it('should display CTA section', () => {
    renderHome();
    
    expect(screen.getByText('Ready to Get Started?')).toBeInTheDocument();
    expect(screen.getByText('Start Your Free Trial Today')).toBeInTheDocument();
  });
});
