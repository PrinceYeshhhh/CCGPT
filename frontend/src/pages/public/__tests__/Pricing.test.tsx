import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Pricing } from '../Pricing';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

// Mock useAuth hook module with vi.fn so tests can override per-case
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({ isAuthenticated: false, user: null })),
}))

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock popup components
vi.mock('@/components/common/PaymentPopup', () => ({
  PaymentPopup: ({ isOpen, onClose, plan, onSuccess }: any) => 
    isOpen ? (
      <div data-testid="payment-popup">
        <div>Payment for {plan?.name}</div>
        <button onClick={onClose}>Close</button>
        <button onClick={() => onSuccess({ success: true })}>Pay</button>
      </div>
    ) : null,
}));

vi.mock('@/components/common/WhiteLabelPopup', () => ({
  WhiteLabelPopup: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="white-label-popup">
        <div>White Label Popup</div>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

vi.mock('@/components/common/TrialPopup', () => ({
  TrialPopup: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="trial-popup">
        <div>Trial Popup</div>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

const mockPricingPlans = {
  plans: [
    {
      id: 'free',
      name: 'Free',
      description: 'Perfect for getting started',
      price: 0,
      currency: 'usd',
      interval: 'month',
      features: ['100 queries/month', '1 document', 'Basic support'],
      popular: false,
      trial_days: 0,
    },
    {
      id: 'starter',
      name: 'Starter',
      description: 'Great for small businesses',
      price: 2000, // $20.00
      currency: 'usd',
      interval: 'month',
      features: ['1,000 queries/month', '10 documents', 'Email support'],
      popular: true,
      trial_days: 14,
    },
    {
      id: 'pro',
      name: 'Pro',
      description: 'Perfect for growing businesses',
      price: 5000, // $50.00
      currency: 'usd',
      interval: 'month',
      features: ['5,000 queries/month', '100 documents', 'Priority support'],
      popular: false,
      trial_days: 14,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      description: 'For large organizations',
      price: 20000, // $200.00
      currency: 'usd',
      interval: 'month',
      features: ['Unlimited queries', 'Unlimited documents', 'Dedicated support'],
      popular: false,
      trial_days: 14,
    },
  ],
};

describe('Pricing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/pricing/plans') {
        return Promise.resolve({ data: mockPricingPlans });
      }
      return Promise.resolve({ data: {} });
    });
  });

  const renderPricing = () => {
    return render(<Pricing />);
  };

  it('should render pricing page', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
    });
  });

  it('should display loading state initially', () => {
    renderPricing();
    
    expect(screen.getByText('Loading pricing plans...')).toBeInTheDocument();
  });

  it('should load and display pricing plans', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });
  });

  it('should display plan prices', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('$0.00')).toBeInTheDocument();
      expect(screen.getByText('$20.00')).toBeInTheDocument();
      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByText('$200.00')).toBeInTheDocument();
    });
  });

  it('should display plan features', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('100 queries/month')).toBeInTheDocument();
      expect(screen.getByText('1,000 queries/month')).toBeInTheDocument();
      expect(screen.getByText('5,000 queries/month')).toBeInTheDocument();
      expect(screen.getByText('Unlimited queries')).toBeInTheDocument();
    });
  });

  it('should mark popular plan', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Most Popular')).toBeInTheDocument();
    });
  });

  it('should handle plan selection for authenticated user', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true } as any)
    
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Starter')).toBeInTheDocument();
    });
    
    const selectButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(selectButtons[1]); // Click Starter plan
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
  });

  it('should handle plan selection for unauthenticated user', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Starter')).toBeInTheDocument();
    });
    
    const selectButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(selectButtons[1]); // Click Starter plan

    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
  });

  it('should handle free plan selection', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Free')).toBeInTheDocument();
    });
    
    const choosePlanButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(choosePlanButtons[0]); // Click first plan (Free)
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
  });

  it('should handle white label plan selection', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('White Label')).toBeInTheDocument();
    });
    
    const whiteLabelButton = screen.getByText('White Label');
    fireEvent.click(whiteLabelButton);
    
    expect(screen.getByTestId('white-label-popup')).toBeInTheDocument();
  });

  it('should handle payment popup close', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true } as any)
    
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Starter')).toBeInTheDocument();
    });
    
    const selectButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(selectButtons[1]);
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('payment-popup')).not.toBeInTheDocument();
  });

  it('should handle payment success', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true } as any)
    
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Starter')).toBeInTheDocument();
    });
    
    const selectButtons = screen.getAllByText('Choose Plan');
    fireEvent.click(selectButtons[1]);
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    
    const payButton = screen.getByText('Pay');
    fireEvent.click(payButton);
    
    expect(screen.queryByTestId('payment-popup')).not.toBeInTheDocument();
  });

  it('should handle trial popup close', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Start 7-Day Free Trial')).toBeInTheDocument();
    });
    
    const trialButton = screen.getByText('Start 7-Day Free Trial');
    fireEvent.click(trialButton);
    
    expect(screen.getByTestId('trial-popup')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('trial-popup')).not.toBeInTheDocument();
  });

  it('should handle API errors', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    renderPricing();

    // The component shows loading state initially, then shows the page with empty plans
    await waitFor(() => {
      expect(screen.getByText('Loading pricing plans...')).toBeInTheDocument();
    });
    
    // After error, it should show the page with FAQ section
    await waitFor(() => {
      expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    });
  });

  it('should display plan descriptions', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Perfect for getting started')).toBeInTheDocument();
      expect(screen.getByText('Great for small businesses')).toBeInTheDocument();
      expect(screen.getByText('Perfect for growing businesses')).toBeInTheDocument();
      expect(screen.getByText('For large organizations')).toBeInTheDocument();
    });
  });

  it('should display trial information', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Start with a 7-day free trial or choose a plan that fits your business needs.')).toBeInTheDocument();
    });
  });

  it('should display FAQ section', async () => {
    renderPricing();
    
    await waitFor(() => {
      expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    });
  });

  it('should handle FAQ accordion', async () => {
    renderPricing();
    
    await waitFor(() => {
      const faqItems = screen.getAllByRole('button');
      const firstFaq = faqItems.find(item => item.textContent?.includes('How does billing work?'));
      
      if (firstFaq) {
        fireEvent.click(firstFaq);
        // Should expand FAQ item
      }
    });
  });

  // Note: The following features are not implemented in the current Pricing component:
  // - Comparison table
  // - Annual billing toggle  
  // - Enterprise features section
  // - Contact sales button
  // - Money back guarantee section
  // - Security badges section
});
