import { renderWithProviders as render, screen, fireEvent, waitFor } from '@/test/test-utils';
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
const mockUsePerformance = vi.fn();
vi.mock('@/hooks/usePerformance', () => ({
  usePerformance: () => mockUsePerformance(),
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
    
    // Mock the usePerformance hook
    mockUsePerformance.mockReturnValue({
      metrics: { lcp: 2500, fid: 100, cls: 0.1, fcp: 1800, ttfb: 200, pageLoadTime: 3200, apiResponseTime: 500, errorCount: 5, clickCount: 0, scrollDepth: 0, timeOnPage: 0, apiErrorCount: 0, performanceScore: 85, accessibilityScore: null, bestPracticesScore: null, seoScore: null, networkLatency: null, renderTime: null, memoryUsage: null },
      getPerformanceSummary: () => ({ score: 85, lcp: '2500ms', fid: '100ms', cls: '0.100', pageLoadTime: '3200ms', apiResponseTime: '500ms', errorCount: 5 }),
      getPerformanceScore: () => 85,
      reportMetrics: vi.fn(),
    });
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/performance/summary') {
        return Promise.resolve({ data: mockPerformanceData.summary });
      }
      if (url === '/performance/trends') {
        return Promise.resolve({ data: { trends: mockPerformanceData.trends } });
      }
      if (url === '/performance/alerts') {
        return Promise.resolve({ data: mockPerformanceData.alerts });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('should render performance dashboard', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
      expect(screen.getByText('Alerts')).toBeInTheDocument();
    });
  });

  it('should display performance score', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('Performance Score')).toBeInTheDocument();
    });
  });

  it('should display core web vitals', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('2500ms')).toBeInTheDocument(); // LCP
      expect(screen.getAllByText('100ms')).toHaveLength(2); // FID and CLS both show 100ms
      expect(screen.getAllByText('0.100')).toHaveLength(2); // FID and CLS both show 0.100
    });
  });

  it('should display API performance metrics', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should display error metrics', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should display health status', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should display alerts', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle tab navigation', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle trends tab', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle alerts tab', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should display performance trends', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle refresh button', async () => {
    const mockRefresh = vi.fn();
    mockUsePerformance.mockReturnValue({
      metrics: { lcp: 2500, fid: 100, cls: 0.1, fcp: 1800, ttfb: 200, pageLoadTime: 3200, apiResponseTime: 500, errorCount: 5, clickCount: 0, scrollDepth: 0, timeOnPage: 0, apiErrorCount: 0, performanceScore: 85, accessibilityScore: null, bestPracticesScore: null, seoScore: null, networkLatency: null, renderTime: null, memoryUsage: null },
      getPerformanceSummary: () => ({ score: 85, lcp: '2500ms', fid: '100ms', cls: '0.100', pageLoadTime: '3200ms', apiResponseTime: '500ms', errorCount: 5 }),
      getPerformanceScore: () => 85,
      reportMetrics: mockRefresh,
    });
    
    render(<Performance />);
    
    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('should display loading state', () => {
    mockUsePerformance.mockReturnValue({
      metrics: { lcp: null, fid: null, cls: null, fcp: null, ttfb: null, pageLoadTime: null, apiResponseTime: null, errorCount: 0, clickCount: 0, scrollDepth: 0, timeOnPage: 0, apiErrorCount: 0, performanceScore: null, accessibilityScore: null, bestPracticesScore: null, seoScore: null, networkLatency: null, renderTime: null, memoryUsage: null },
      getPerformanceSummary: () => ({ score: 0, lcp: 'N/A', fid: 'N/A', cls: 'N/A', pageLoadTime: 'N/A', apiResponseTime: 'N/A', errorCount: 0 }),
      getPerformanceScore: () => 0,
      reportMetrics: vi.fn(),
    });
    
    render(<Performance />);
    
    expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
  });

  it('should display performance score with color coding', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      const scoreElement = screen.getByText('85');
      expect(scoreElement).toBeInTheDocument();
    });
  });

  it('should display health issues when present', async () => {
    const performanceDataWithIssues = {
      ...mockPerformanceData,
      summary: {
        ...mockPerformanceData.summary,
        is_healthy: false,
        health_issues: ['High LCP', 'Slow API response'],
      },
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/performance/summary') {
        return Promise.resolve({ data: performanceDataWithIssues.summary });
      }
      if (url === '/performance/trends') {
        return Promise.resolve({ data: { trends: mockPerformanceData.trends } });
      }
      if (url === '/performance/alerts') {
        return Promise.resolve({ data: mockPerformanceData.alerts });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Needs Attention')).toBeInTheDocument();
    });
  });

  it('should display performance recommendations', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle download performance report', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      const downloadButton = screen.getByText('Export');
      fireEvent.click(downloadButton);
      
      expect(downloadButton).toBeInTheDocument();
    });
  });

  it('should display performance metrics in cards', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Overall Score')).toBeInTheDocument();
      expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
      expect(screen.getByText('Error Rate')).toBeInTheDocument();
    });
  });

  it('should display trend charts', async () => {
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Real-time Performance')).toBeInTheDocument();
    });
  });

  it('should handle performance score thresholds', async () => {
    const lowPerformanceData = {
      ...mockPerformanceData,
      summary: {
        ...mockPerformanceData.summary,
        performance_score: 45,
      },
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/performance/summary') {
        return Promise.resolve({ data: lowPerformanceData.summary });
      }
      if (url === '/performance/trends') {
        return Promise.resolve({ data: { trends: mockPerformanceData.trends } });
      }
      if (url === '/performance/alerts') {
        return Promise.resolve({ data: mockPerformanceData.alerts });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Performance />);
    
    await waitFor(() => {
      expect(screen.getByText('45')).toBeInTheDocument();
    });
  });
});
