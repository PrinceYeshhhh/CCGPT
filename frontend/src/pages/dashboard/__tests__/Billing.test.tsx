import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
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
      popular: false,
    },
    {
      id: 'pro',
      name: 'Pro',
      price: 5000, // $50.00
      currency: 'usd',
      interval: 'month',
      features: ['5000 queries', '100 documents', '10GB storage'],
      popular: true,
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

  it('should render loading state initially', () => {
    render(<Billing />);
    
    expect(screen.getByText('Loading billing information...')).toBeInTheDocument();
  });

  it('should load and display billing information', async () => {
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Billing & Usage')).toBeInTheDocument();
      expect(screen.getByText('Current Plan')).toBeInTheDocument();
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('$50')).toBeInTheDocument();
      expect(screen.getByText('per month')).toBeInTheDocument();
    });
  });

  it('should display usage information', async () => {
    render(<Billing />);
    
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
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Payment Method')).toBeInTheDocument();
      expect(screen.getByText('VISA •••• •••• •••• 4242')).toBeInTheDocument();
      expect(screen.getByText('Expires 12/2025 • Default')).toBeInTheDocument();
    });
  });

  it('should display billing history', async () => {
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Billing History')).toBeInTheDocument();
      expect(screen.getByText('Pro Plan - January 2024')).toBeInTheDocument();
      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByText('paid')).toBeInTheDocument();
    });
  });

  it('should display pricing plans', async () => {
    render(<Billing />);
    
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
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Current Plan')).toBeInTheDocument();
      expect(screen.getByText('Popular')).toBeInTheDocument();
    });
  });

  it('should handle plan upgrade', async () => {
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Upgrade')).toBeInTheDocument();
    });
    
    const upgradeButtons = screen.getAllByText('Upgrade');
    fireEvent.click(upgradeButtons[0]); // Click first upgrade button
    
    expect(screen.getByTestId('payment-popup')).toBeInTheDocument();
    expect(screen.getByText('Payment for Starter')).toBeInTheDocument();
  });

  it('should handle payment success', async () => {
    render(<Billing />);
    
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
    render(<Billing />);
    
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
    render(<Billing />);
    
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
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Billing History')).toBeInTheDocument();
    });
    
    const downloadButtons = screen.getAllByRole('button');
    const downloadButton = downloadButtons.find(btn => btn.querySelector('svg'));
    if (downloadButton) {
      fireEvent.click(downloadButton);
      expect(mockOpen).toHaveBeenCalledWith('https://example.com/invoice.pdf', '_blank');
    }
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
    
    const mockCreateElement = vi.fn(() => ({
      href: '',
      download: '',
      click: vi.fn(),
      setAttribute: vi.fn(),
    }));
    
    Object.defineProperty(document, 'createElement', {
      value: mockCreateElement,
      writable: true,
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: vi.fn(),
      writable: true,
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: vi.fn(),
      writable: true,
    });
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/invoices/download-all') {
        return Promise.resolve({ data: mockBlob });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Download All Invoices')).toBeInTheDocument();
    });
    
    const downloadAllButton = screen.getByText('Download All Invoices');
    fireEvent.click(downloadAllButton);
    
    expect(mockApi.get).toHaveBeenCalledWith('/billing/invoices/download-all', {
      responseType: 'blob',
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
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('High Usage Alert')).toBeInTheDocument();
      expect(screen.getByText("You've used 90% of your monthly query limit")).toBeInTheDocument();
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
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Trial')).toBeInTheDocument();
      expect(screen.getByText('Trial ends 2/1/2024')).toBeInTheDocument();
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
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('forever')).toBeInTheDocument();
      expect(screen.getByText('No payment required')).toBeInTheDocument();
    });
  });

  it('should handle error state', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('Unable to load billing information')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('should handle retry after error', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(<Billing />);
    
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
      if (url === '/billing/payment-methods') {
        return Promise.resolve({ data: noPaymentMethods });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('No Payment Method')).toBeInTheDocument();
      expect(screen.getByText('Add a payment method to manage your subscription')).toBeInTheDocument();
    });
  });

  it('should handle no invoices', async () => {
    const noInvoices = {
      invoices: [],
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/invoices') {
        return Promise.resolve({ data: noInvoices });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Billing />);
    
    await waitFor(() => {
      expect(screen.getByText('No Invoices')).toBeInTheDocument();
      expect(screen.getByText('Your billing history will appear here once you have active subscriptions')).toBeInTheDocument();
    });
  });
});
