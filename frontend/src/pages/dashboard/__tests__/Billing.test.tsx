import { screen, fireEvent, waitFor, cleanup, act } from '@testing-library/react';
import { renderWithProviders as render } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Billing } from '../Billing';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

// Mock PaymentPopup component
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

// Mock Progress component
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, className }: { value: number; className?: string }) => (
    <div data-testid="progress" className={className} style={{ width: `${value}%` }}>
      {value}%
    </div>
  ),
}));

// Mock Badge component
vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: { children: React.ReactNode; variant?: string; className?: string }) => (
    <span data-testid="badge" className={className}>
      {children}
    </span>
  ),
}));

// Mock Card components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-header" className={className}>
      {children}
    </div>
  ),
  CardTitle: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <h3 data-testid="card-title" className={className}>
      {children}
    </h3>
  ),
  CardDescription: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <p data-testid="card-description" className={className}>
      {children}
    </p>
  ),
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-content" className={className}>
      {children}
    </div>
  ),
}));

// Mock Button component
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, className, size, variant }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    disabled?: boolean; 
    className?: string; 
    size?: string; 
    variant?: string; 
  }) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      disabled={disabled} 
      className={className}
    >
      {children}
    </button>
  ),
}));

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
  CreditCard: () => <div data-testid="credit-card-icon" />,
  Download: () => <div data-testid="download-icon" />,
  Calendar: () => <div data-testid="calendar-icon" />,
  AlertCircle: () => <div data-testid="alert-circle-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  ArrowUpRight: () => <div data-testid="arrow-up-right-icon" />,
  Receipt: () => <div data-testid="receipt-icon" />,
  Zap: () => <div data-testid="zap-icon" />,
  Loader2: () => <div data-testid="loader2-icon" />,
  RefreshCw: () => <div data-testid="refresh-cw-icon" />,
}));

const mockApi = vi.mocked(api);

const mockBillingData = {
  plan: 'pro',
  status: 'active',
  current_period_end: '2024-02-01',
  cancel_at_period_end: false,
  usage: {
    queries_used: 750,
    queries_limit: 1000,
    documents_used: 5,
    documents_limit: 50,
    storage_used: 1073741824, // 1GB in bytes
    storage_limit: 5368709120, // 5GB in bytes
  },
  billing_portal_url: 'https://billing.example.com',
  trial_end: null,
  is_trial: false,
};

const mockPricingPlans = {
  plans: [
    {
      id: 'starter',
      name: 'Starter',
      price: 2000, // $20.00
      currency: 'usd',
      interval: 'month',
      features: ['1000 queries', '10 documents', '1GB storage'],
      popular: true, // Make Starter popular since Pro is current plan
    },
    {
      id: 'pro',
      name: 'Pro',
      price: 5000, // $50.00
      currency: 'usd',
      interval: 'month',
      features: ['5000 queries', '100 documents', '10GB storage'],
      popular: false, // Not popular since it's the current plan
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 20000, // $200.00
      currency: 'usd',
      interval: 'month',
      features: ['Unlimited queries', 'Unlimited documents', 'Unlimited storage'],
      popular: false,
    },
  ],
};

const mockPaymentMethods = {
  payment_methods: [
    {
      id: 'pm_123',
      type: 'card',
      last4: '4242',
      brand: 'visa',
      exp_month: 12,
      exp_year: 2025,
      is_default: true,
    },
  ],
};

const mockInvoices = {
  invoices: [
    {
      id: 'in_123',
      amount: 5000,
      currency: 'usd',
      status: 'paid',
      created: '2024-01-01T00:00:00Z',
      invoice_pdf: 'https://example.com/invoice.pdf',
      description: 'Pro Plan - January 2024',
    },
  ],
};

describe('Billing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: mockBillingData });
      }
      if (url === '/pricing/plans') {
        return Promise.resolve({ data: mockPricingPlans });
      }
      if (url === '/billing/payment-methods') {
        return Promise.resolve({ data: mockPaymentMethods });
      }
      if (url === '/billing/invoices') {
        return Promise.resolve({ data: mockInvoices });
      }
      return Promise.resolve({ data: {} });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('should render loading state initially', () => {
    act(() => {
      act(() => {
      render(<Billing />);
    });
    });
    
    expect(screen.getByText('Loading billing information...')).toBeInTheDocument();
  });

  it('should load and display billing information', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Billing & Usage' })).toBeInTheDocument();
      expect(screen.getByText('Current Plan')).toBeInTheDocument();
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('$50')).toBeInTheDocument();
      expect(screen.getByText('per month')).toBeInTheDocument();
    });
  });

  it('should display usage information', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('750 used')).toBeInTheDocument();
      expect(screen.getByText('1,000 limit')).toBeInTheDocument();
      expect(screen.getByText('5 used')).toBeInTheDocument();
      expect(screen.getByText('50 limit')).toBeInTheDocument();
      expect(screen.getByText('1.0 GB used')).toBeInTheDocument();
      expect(screen.getByText('5.0 GB limit')).toBeInTheDocument();
    });
  });

  it('should display payment method information', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Payment Method')).toBeInTheDocument();
      expect(screen.getByText('VISA •••• •••• •••• 4242')).toBeInTheDocument();
      expect(screen.getByText('Expires 12/2025 • Default')).toBeInTheDocument();
    });
  });

  it('should display billing history', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Billing History')).toBeInTheDocument();
      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByText('Pro Plan - January 2024')).toBeInTheDocument();
      expect(screen.getByText('paid')).toBeInTheDocument();
    });
  });

  it('should display pricing plans', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Upgrade Your Plan')).toBeInTheDocument();
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
      expect(screen.getByText('$20.00')).toBeInTheDocument();
      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByText('$200.00')).toBeInTheDocument();
    });
  });

  it('should mark current plan correctly', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Current Plan')).toBeInTheDocument();
      // Current plan should show "Pro" and "active" status
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
      // Popular badge should be visible in the pricing plans section for non-current plans
      // Since Pro is the current plan, Popular badge should not show for Pro
      // But it should show for other plans that have popular: true
      expect(screen.getByText('Popular')).toBeInTheDocument();
    });
  });

  it('should handle plan upgrade', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Upgrade')).toBeInTheDocument();
    });
    const upgradeButtons = screen.getAllByText('Upgrade');
    fireEvent.click(upgradeButtons[0]); // Click first upgrade button
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    expect(screen.getByText('Payment for Starter')).toBeInTheDocument();
  });

  it('should handle payment success', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Upgrade')).toBeInTheDocument();
    });
    
    const upgradeButtons = screen.getAllByText('Upgrade');
    fireEvent.click(upgradeButtons[0]);
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    
    const payButton = screen.getByText('Pay');
    fireEvent.click(payButton);
    
    expect(screen.queryByTestId('payment-popup')).not.toBeInTheDocument();
  });

  it('should handle payment popup close', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Upgrade')).toBeInTheDocument();
    });
    
    const upgradeButtons = screen.getAllByText('Upgrade');
    fireEvent.click(upgradeButtons[0]);
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('payment-popup')).not.toBeInTheDocument();
  });

  it('should handle refresh button', async () => {
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should make API calls again
    expect(mockApi.get).toHaveBeenCalledWith('/billing/status');
  });

  it('should handle download invoice', async () => {
    // Mock window.open
    const mockOpen = vi.fn();
    Object.defineProperty(window, 'open', {
      value: mockOpen,
      writable: true,
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Billing History')).toBeInTheDocument();
    });
    
    const downloadButton = screen.getByRole('button', { name: 'Download invoice in_123' });
    fireEvent.click(downloadButton);
    expect(mockOpen).toHaveBeenCalledWith('https://example.com/invoice.pdf', '_blank');
  });

  it('should handle download all invoices', async () => {
    // Mock blob and URL.createObjectURL
    const mockBlob = new Blob(['test'], { type: 'application/zip' });
    const mockUrl = 'blob:test-url';
    
    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: vi.fn(() => mockUrl),
        revokeObjectURL: vi.fn(),
      },
      writable: true,
    });
    
    // Store original methods
    const originalCreateElement = document.createElement;
    const originalAppendChild = document.body.appendChild;
    const originalRemoveChild = document.body.removeChild;
    
    const mockCreateElement = vi.fn((tagName) => {
      if (tagName === 'a') {
        return {
          href: '',
          download: '',
          click: vi.fn(),
          setAttribute: vi.fn(),
        };
      }
      // For other elements, use the original createElement
      return originalCreateElement.call(document, tagName);
    });
    
    const mockAppendChild = vi.fn((element) => {
      // Only mock for anchor elements
      if (element.tagName === 'A') {
        return element;
      }
      // For other elements, use the original appendChild
      return originalAppendChild.call(document.body, element);
    });
    
    const mockRemoveChild = vi.fn((element) => {
      // Only mock for anchor elements
      if (element.tagName === 'A') {
        return element;
      }
      // For other elements, use the original removeChild
      return originalRemoveChild.call(document.body, element);
    });
    
    Object.defineProperty(document, 'createElement', {
      value: mockCreateElement,
      writable: true,
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild,
      writable: true,
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild,
      writable: true,
    });
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: mockBillingData });
      }
      if (url === '/pricing/plans') {
        return Promise.resolve({ data: mockPricingPlans });
      }
      if (url === '/billing/payment-methods') {
        return Promise.resolve({ data: mockPaymentMethods });
      }
      if (url === '/billing/invoices') {
        return Promise.resolve({ data: mockInvoices });
      }
      if (url === '/billing/invoices/download-all') {
        return Promise.resolve({ data: mockBlob });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Download All Invoices')).toBeInTheDocument();
    });
    
    const downloadAllButton = screen.getByText('Download All Invoices');
    fireEvent.click(downloadAllButton);
    
    expect(mockApi.get).toHaveBeenCalledWith('/billing/invoices/download-all', {
      responseType: 'blob',
    });
    
    // Restore original methods
    Object.defineProperty(document, 'createElement', {
      value: originalCreateElement,
      writable: true,
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: originalAppendChild,
      writable: true,
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: originalRemoveChild,
      writable: true,
    });
  });

  it('should display high usage warning', async () => {
    const highUsageBillingData = {
      ...mockBillingData,
      usage: {
        ...mockBillingData.usage,
        queries_used: 900,
        queries_limit: 1000,
      },
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: highUsageBillingData });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('High Usage Alert')).toBeInTheDocument();
      expect(screen.getByText("You've used 90% of your monthly query limit. Consider upgrading to avoid service interruption.")).toBeInTheDocument();
    });
  });

  it('should handle trial billing info', async () => {
    const trialBillingData = {
      ...mockBillingData,
      is_trial: true,
      trial_end: '2024-02-01',
      status: 'trialing',
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: trialBillingData });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Trial')).toBeInTheDocument();
      expect(screen.getByText('Trial ends 1/2/2024')).toBeInTheDocument();
      expect(screen.getByText("You're currently on the Pro plan (7-day free trial)")).toBeInTheDocument();
    });
  });

  it('should handle free plan', async () => {
    const freeBillingData = {
      ...mockBillingData,
      plan: 'free',
      status: 'active',
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: freeBillingData });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('forever')).toBeInTheDocument();
      expect(screen.getByText('No payment required')).toBeInTheDocument();
    });
  });

  it('should handle error state', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Unable to load billing information')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('should handle retry after error', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
    
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);
    
    expect(mockApi.get).toHaveBeenCalledWith('/billing/status');
  });

  it('should handle no payment methods', async () => {
    const noPaymentMethods = {
      payment_methods: [],
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: mockBillingData });
      }
      if (url === '/pricing/plans') {
        return Promise.resolve({ data: mockPricingPlans });
      }
      if (url === '/billing/payment-methods') {
        return Promise.resolve({ data: noPaymentMethods });
      }
      if (url === '/billing/invoices') {
        return Promise.resolve({ data: mockInvoices });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getAllByText('No Payment Method')).toHaveLength(1);
      expect(screen.getByText('Add a payment method to manage your subscription')).toBeInTheDocument();
    });
  });

  it('should handle no invoices', async () => {
    const noInvoices = {
      invoices: [],
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: mockBillingData });
      }
      if (url === '/pricing/plans') {
        return Promise.resolve({ data: mockPricingPlans });
      }
      if (url === '/billing/payment-methods') {
        return Promise.resolve({ data: mockPaymentMethods });
      }
      if (url === '/billing/invoices') {
        return Promise.resolve({ data: noInvoices });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Billing />);
    });
    
    await waitFor(() => {
      expect(screen.getAllByText('No Invoices')).toHaveLength(1);
      expect(screen.getByText('Your billing history will appear here once you have active subscriptions')).toBeInTheDocument();
    });
  });
});
