import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Performance } from '../Performance';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

// Mock usePerformance hook
vi.mock('@/hooks/usePerformance', () => ({
  usePerformance: () => ({
    performanceData: {
      summary: {
        performance_score: 85,
        avg_lcp: 2.5,
        avg_fid: 100,
        avg_cls: 0.1,
        avg_fcp: 1.8,
        avg_ttfb: 200,
        avg_page_load_time: 3.2,
        avg_api_response_time: 500,
        total_errors: 5,
        error_rate: 0.02,
        is_healthy: true,
        health_issues: [],
      },
      trends: {
        lcp: [{ date: '2024-01-01', value: 2.5 }],
        fid: [{ date: '2024-01-01', value: 100 }],
        cls: [{ date: '2024-01-01', value: 0.1 }],
        errors: [{ date: '2024-01-01', value: 5 }],
      },
      alerts: [
        {
          id: 'alert1',
          alert_type: 'performance',
          severity: 'warning',
          message: 'High LCP detected',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    },
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

// Mock recharts components
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

const mockApi = vi.mocked(api);

const mockPerformanceData = {
  summary: {
    performance_score: 85,
    avg_lcp: 2.5,
    avg_fid: 100,
    avg_cls: 0.1,
    avg_fcp: 1.8,
    avg_ttfb: 200,
    avg_page_load_time: 3.2,
    avg_api_response_time: 500,
    total_errors: 5,
    error_rate: 0.02,
    is_healthy: true,
    health_issues: [],
  },
  trends: {
    lcp: [{ date: '2024-01-01', value: 2.5 }],
    fid: [{ date: '2024-01-01', value: 100 }],
    cls: [{ date: '2024-01-01', value: 0.1 }],
    errors: [{ date: '2024-01-01', value: 5 }],
  },
  alerts: [
    {
      id: 'alert1',
      alert_type: 'performance',
      severity: 'warning',
      message: 'High LCP detected',
      created_at: '2024-01-01T00:00:00Z',
    },
  ],
};

describe('Performance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/performance/summary') {
        return Promise.resolve({ data: mockPerformanceData });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('should render performance dashboard', () => {
    render(<Performance />);
    
    expect(screen.getByText('Performance Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
    expect(screen.getByText('API Performance')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });

  it('should display performance score', () => {
    render(<Performance />);
    
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Performance Score')).toBeInTheDocument();
  });

  it('should display core web vitals', () => {
    render(<Performance />);
    
    expect(screen.getByText('2.5s')).toBeInTheDocument(); // LCP
    expect(screen.getByText('100ms')).toBeInTheDocument(); // FID
    expect(screen.getByText('0.1')).toBeInTheDocument(); // CLS
  });

  it('should display API performance metrics', () => {
    render(<Performance />);
    
    expect(screen.getByText('500ms')).toBeInTheDocument(); // API response time
    expect(screen.getByText('3.2s')).toBeInTheDocument(); // Page load time
  });

  it('should display error metrics', () => {
    render(<Performance />);
    
    expect(screen.getByText('5')).toBeInTheDocument(); // Total errors
    expect(screen.getByText('2%')).toBeInTheDocument(); // Error rate
  });

  it('should display health status', () => {
    render(<Performance />);
    
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('should display alerts', () => {
    render(<Performance />);
    
    expect(screen.getByText('High LCP detected')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  it('should handle tab navigation', () => {
    render(<Performance />);
    
    const coreWebVitalsTab = screen.getByText('Core Web Vitals');
    fireEvent.click(coreWebVitalsTab);
    
    expect(screen.getByText('Largest Contentful Paint (LCP)')).toBeInTheDocument();
    expect(screen.getByText('First Input Delay (FID)')).toBeInTheDocument();
    expect(screen.getByText('Cumulative Layout Shift (CLS)')).toBeInTheDocument();
  });

  it('should handle API performance tab', () => {
    render(<Performance />);
    
    const apiPerformanceTab = screen.getByText('API Performance');
    fireEvent.click(apiPerformanceTab);
    
    expect(screen.getByText('API Response Time')).toBeInTheDocument();
    expect(screen.getByText('Page Load Time')).toBeInTheDocument();
  });

  it('should handle alerts tab', () => {
    render(<Performance />);
    
    const alertsTab = screen.getByText('Alerts');
    fireEvent.click(alertsTab);
    
    expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
  });

  it('should display performance trends', () => {
    render(<Performance />);
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('should handle refresh button', () => {
    const mockRefresh = vi.fn();
    vi.mocked(require('@/hooks/usePerformance').usePerformance).mockReturnValue({
      performanceData: mockPerformanceData,
      loading: false,
      error: null,
      refresh: mockRefresh,
    });
    
    render(<Performance />);
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    expect(mockRefresh).toHaveBeenCalled();
  });

  it('should display loading state', () => {
    vi.mocked(require('@/hooks/usePerformance').usePerformance).mockReturnValue({
      performanceData: null,
      loading: true,
      error: null,
      refresh: vi.fn(),
    });
    
    render(<Performance />);
    
    expect(screen.getByText('Loading performance data...')).toBeInTheDocument();
  });

  it('should display error state', () => {
    vi.mocked(require('@/hooks/usePerformance').usePerformance).mockReturnValue({
      performanceData: null,
      loading: false,
      error: 'Failed to load performance data',
      refresh: vi.fn(),
    });
    
    render(<Performance />);
    
    expect(screen.getByText('Failed to load performance data')).toBeInTheDocument();
  });

  it('should display performance score with color coding', () => {
    render(<Performance />);
    
    const scoreElement = screen.getByText('85');
    expect(scoreElement).toBeInTheDocument();
  });

  it('should display health issues when present', () => {
    const performanceDataWithIssues = {
      ...mockPerformanceData,
      summary: {
        ...mockPerformanceData.summary,
        is_healthy: false,
        health_issues: ['High LCP', 'Slow API response'],
      },
    };
    
    vi.mocked(require('@/hooks/usePerformance').usePerformance).mockReturnValue({
      performanceData: performanceDataWithIssues,
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    
    render(<Performance />);
    
    expect(screen.getByText('Unhealthy')).toBeInTheDocument();
  });

  it('should display performance recommendations', () => {
    render(<Performance />);
    
    expect(screen.getByText('Performance Recommendations')).toBeInTheDocument();
  });

  it('should handle download performance report', () => {
    render(<Performance />);
    
    const downloadButton = screen.getByText('Download Report');
    fireEvent.click(downloadButton);
    
    // Should trigger download
    expect(downloadButton).toBeInTheDocument();
  });

  it('should display performance metrics in cards', () => {
    render(<Performance />);
    
    expect(screen.getByText('Performance Score')).toBeInTheDocument();
    expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
    expect(screen.getByText('API Performance')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
  });

  it('should display trend charts', () => {
    render(<Performance />);
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('should handle performance score thresholds', () => {
    const lowPerformanceData = {
      ...mockPerformanceData,
      summary: {
        ...mockPerformanceData.summary,
        performance_score: 45,
      },
    };
    
    vi.mocked(require('@/hooks/usePerformance').usePerformance).mockReturnValue({
      performanceData: lowPerformanceData,
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    
    render(<Performance />);
    
    expect(screen.getByText('45')).toBeInTheDocument();
  });
});
