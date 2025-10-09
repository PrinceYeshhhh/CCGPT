import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Overview } from '../Overview';
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

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
  },
}));

// Mock components
vi.mock('@/components/common/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div data-testid="error-boundary">{children}</div>,
}));

vi.mock('@/components/common/LoadingStates', () => ({
  LoadingCard: ({ title }: { title?: string }) => <div data-testid="loading-card">{title || 'Loading...'}</div>,
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
  LoadingChart: () => <div data-testid="loading-chart">Loading chart...</div>,
}));

vi.mock('@/components/dashboard/CurrentPlanDisplay', () => ({
  CurrentPlanDisplay: ({ plan, status, isTrial, trialEnd, className }: any) => (
    <div data-testid="current-plan-display" className={className}>
      Plan: {plan}, Status: {status}, Trial: {isTrial ? 'Yes' : 'No'}
      {trialEnd && `, Ends: ${trialEnd}`}
    </div>
  ),
}));

// Mock recharts components
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

const mockApi = vi.mocked(api);

const mockOverviewData = {
  total_messages: 1500,
  active_sessions: 25,
  avg_response_time: 2500,
  top_questions: [
    { question: 'How do I reset my password?', count: 45 },
    { question: 'What are your business hours?', count: 32 },
    { question: 'How can I contact support?', count: 28 },
  ],
};

const mockUsageData = [
  { date: '2024-01-01', messages_count: 100 },
  { date: '2024-01-02', messages_count: 150 },
  { date: '2024-01-03', messages_count: 200 },
];

const mockKpisData = {
  queries: { delta_pct: 12.5 },
  sessions: { delta_pct: 8.3 },
  avg_response_time_ms: { delta_ms: -300 },
  active_sessions: { delta: 5 },
};

const mockBillingData = {
  plan: 'pro',
  status: 'active',
  is_trial: false,
  trial_end: null,
  usage: {
    queries_used: 750,
    queries_limit: 1000,
  },
};

describe('Overview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/analytics/overview') {
        return Promise.resolve({ data: mockOverviewData });
      }
      if (url === '/analytics/usage-stats' && url.includes('days=7')) {
        return Promise.resolve({ data: mockUsageData });
      }
      if (url === '/analytics/usage-stats' && url.includes('days=30')) {
        return Promise.resolve({ data: mockUsageData });
      }
      if (url === '/analytics/kpis') {
        return Promise.resolve({ data: mockKpisData });
      }
      if (url === '/billing/status') {
        return Promise.resolve({ data: mockBillingData });
      }
      return Promise.resolve({ data: {} });
    });
  });

  const renderOverview = () => {
    return render(
      <BrowserRouter>
        <Overview />
      </BrowserRouter>
    );
  };

  it('should render loading state initially', () => {
    renderOverview();
    
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    expect(screen.getByTestId('loading-card')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
    expect(screen.getByText('Upgrade Plan')).toBeInTheDocument();
  });

  it('should load and display data after API calls', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('1,500')).toBeInTheDocument(); // totalQueries
      expect(screen.getByText('750')).toBeInTheDocument(); // queriesThisMonth
      expect(screen.getByText('25')).toBeInTheDocument(); // activeUsers
      expect(screen.getByText('2.5s')).toBeInTheDocument(); // avgResponseTime
    });
  });

  it('should display current plan information', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByTestId('current-plan-display')).toBeInTheDocument();
      expect(screen.getByText('Plan: pro, Status: active, Trial: No')).toBeInTheDocument();
    });
  });

  it('should display usage progress bar', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('750 / 1000')).toBeInTheDocument();
      expect(screen.getByText('25% remaining')).toBeInTheDocument();
    });
  });

  it('should display top questions', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Top Questions This Month')).toBeInTheDocument();
      expect(screen.getByText('How do I reset my password?')).toBeInTheDocument();
      expect(screen.getByText('45 times')).toBeInTheDocument();
    });
  });

  it('should display chart data', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('should handle refresh button click', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('1,500')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should show refreshing state
    expect(screen.getByText('Refresh')).toBeInTheDocument();
  });

  it('should handle upgrade plan button click', async () => {
    renderOverview();
    
    await waitFor(() => {
      const upgradeButton = screen.getByText('Upgrade Plan');
      fireEvent.click(upgradeButton);
      expect(mockNavigate).toHaveBeenCalledWith('/pricing');
    });
  });

  it('should display error state when API fails', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('should handle retry button click', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    });
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    
    // Should retry the API call
    expect(mockApi.get).toHaveBeenCalledTimes(6); // 5 initial calls + 1 retry
  });

  it('should show high usage warning when over 80%', async () => {
    const highUsageBillingData = {
      ...mockBillingData,
      usage: {
        queries_used: 850,
        queries_limit: 1000,
      },
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: highUsageBillingData });
      }
      return Promise.resolve({ data: {} });
    });
    
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('High usage - consider upgrading')).toBeInTheDocument();
    });
  });

  it('should format delta percentages correctly', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('+12.5% from previous period')).toBeInTheDocument();
      expect(screen.getByText('+8.3% from previous period')).toBeInTheDocument();
      expect(screen.getByText('+5 from previous period')).toBeInTheDocument();
    });
  });

  it('should format response time delta correctly', async () => {
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('-0.3s from previous period')).toBeInTheDocument();
    });
  });

  it('should handle empty top questions', async () => {
    const emptyOverviewData = {
      ...mockOverviewData,
      top_questions: [],
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/analytics/overview') {
        return Promise.resolve({ data: emptyOverviewData });
      }
      return Promise.resolve({ data: {} });
    });
    
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Top Questions This Month')).toBeInTheDocument();
      // Should not crash with empty questions
    });
  });

  it('should handle trial billing info', async () => {
    const trialBillingData = {
      ...mockBillingData,
      is_trial: true,
      trial_end: '2024-02-01',
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/billing/status') {
        return Promise.resolve({ data: trialBillingData });
      }
      return Promise.resolve({ data: {} });
    });
    
    renderOverview();
    
    await waitFor(() => {
      expect(screen.getByText('Plan: pro, Status: active, Trial: Yes, Ends: 2024-02-01')).toBeInTheDocument();
    });
  });
});
