import { screen, fireEvent, waitFor, act, render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Analytics } from '../Analytics';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

// Mock recharts components
vi.mock('recharts', () => ({
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

// Mock Radix UI Tabs components
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue }: { children: React.ReactNode; defaultValue?: string }) => <div data-testid="tabs" data-default-value={defaultValue}>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => <button data-testid={`tab-trigger-${value}`}>{children}</button>,
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => <div data-testid={`tab-content-${value}`}>{children}</div>,
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => {
  const MockIcon = ({ className }: { className?: string }) => <svg className={className} data-testid="mock-icon" />;
  return {
    Download: MockIcon,
    TrendingUp: MockIcon,
    Users: MockIcon,
    MessageSquare: MockIcon,
    Clock: MockIcon,
    Filter: MockIcon,
    Calendar: MockIcon,
  };
});

const mockApi = vi.mocked(api);

const mockAnalyticsData = {
  data: {
    data: {
      total_queries: 2500,
      unique_users: 150,
      avg_response_time: 1.8,
      satisfaction_rate: 87.5,
    },
  },
};

const mockUsageData = {
  data: {
    data: [
      { date: '2024-01-01', queries: 100, satisfied: 85, unsatisfied: 15 },
      { date: '2024-01-02', queries: 150, satisfied: 130, unsatisfied: 20 },
    ],
  },
};

const mockHourlyData = {
  data: {
    data: [
      { hour: '00:00', queries: 10 },
      { hour: '01:00', queries: 5 },
      { hour: '02:00', queries: 8 },
    ],
  },
};

const mockSatisfactionData = {
  data: {
    data: [
      { date: '2024-01-01', satisfied: 200, unsatisfied: 30 },
      { date: '2024-01-02', satisfied: 150, unsatisfied: 20 },
    ],
  },
};

const mockTopQuestionsData = {
  data: {
    data: [
      { question: 'How do I reset my password?', count: 45, satisfaction: 90 },
      { question: 'What are your business hours?', count: 32, satisfaction: 85 },
    ],
  },
};

const mockExportData = {
  data: {
    queries: 2500,
    users: 150,
    satisfaction: 87.5,
  },
};

describe('Analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url, options) => {
      console.log('API call:', url, options);
      if (url === '/analytics/detailed-overview') {
        console.log('Returning overview data:', mockAnalyticsData);
        return Promise.resolve(mockAnalyticsData);
      }
      if (url === '/analytics/detailed-usage-stats') {
        console.log('Returning usage data:', mockUsageData);
        return Promise.resolve(mockUsageData);
      }
      if (url === '/analytics/detailed-hourly') {
        console.log('Returning hourly data:', mockHourlyData);
        return Promise.resolve(mockHourlyData);
      }
      if (url === '/analytics/detailed-satisfaction') {
        console.log('Returning satisfaction data:', mockSatisfactionData);
        return Promise.resolve(mockSatisfactionData);
      }
      if (url === '/analytics/detailed-top-questions') {
        console.log('Returning top questions data:', mockTopQuestionsData);
        return Promise.resolve(mockTopQuestionsData);
      }
      if (url === '/analytics/detailed-export') {
        console.log('Returning export data:', mockExportData);
        return Promise.resolve(mockExportData);
      }
      console.log('Returning empty data for:', url);
      return Promise.resolve({ data: {} });
    });
  });

  it('should render loading state initially', () => {
    render(<Analytics />);
    
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Filter')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByText('7 days')).toBeInTheDocument();
    expect(screen.getByText('30 days')).toBeInTheDocument();
    expect(screen.getByText('90 days')).toBeInTheDocument();
  });

  it('should load and display metrics after API calls', async () => {
    render(<Analytics />);
    
    // Check if component rendered
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    
    // Check if metrics cards are rendered
    expect(screen.getByText('Total Queries')).toBeInTheDocument();
    expect(screen.getByText('Unique Users')).toBeInTheDocument();
    expect(screen.getByText('Avg Response Time')).toBeInTheDocument();
    expect(screen.getByText('Satisfaction Rate')).toBeInTheDocument();
    
    // Initially should show loading state
    expect(screen.getAllByText('...')).toHaveLength(4);
    
    // Wait for loading to complete and data to be displayed
    await waitFor(() => {
      expect(screen.getByText('2,500')).toBeInTheDocument(); // totalQueries
    }, { timeout: 10000 });
    
    expect(screen.getByText('150')).toBeInTheDocument(); // uniqueUsers
    expect(screen.getByText('1.8s')).toBeInTheDocument(); // avgResponseTime
    expect(screen.getByText('87.5%')).toBeInTheDocument(); // satisfactionRate
  });

  it('should display loading state for metrics', () => {
    render(<Analytics />);
    
    expect(screen.getAllByText('...')).toHaveLength(4); // All metrics show loading
  });

  it('should handle time range changes', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('2,500')).toBeInTheDocument();
    });
    
    const thirtyDaysButton = screen.getByText('30 days');
    fireEvent.click(thirtyDaysButton);
    
    // Should make new API calls with 30 days parameter
    expect(mockApi.get).toHaveBeenCalledWith('/analytics/detailed-overview', { params: { days: 30 } });
  });

  it('should handle 90 days time range', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('2,500')).toBeInTheDocument();
    });
    
    const ninetyDaysButton = screen.getByText('90 days');
    fireEvent.click(ninetyDaysButton);
    
    expect(mockApi.get).toHaveBeenCalledWith('/analytics/detailed-overview', { params: { days: 90 } });
  });

  it('should display tabs for different chart views', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
      expect(screen.getByText('Satisfaction')).toBeInTheDocument();
      expect(screen.getByText('Hourly Trends')).toBeInTheDocument();
      // "Top Questions" appears in tab trigger and section heading; ensure at least one is present
      expect(screen.getAllByText('Top Questions').length).toBeGreaterThan(0);
    });
  });

  it('should display query volume chart', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume Over Time')).toBeInTheDocument();
      expect(screen.getAllByTestId('area-chart')).toHaveLength(2); // Multiple AreaChart components
    });
  });

  it('should display satisfaction chart', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
    });
    
    const satisfactionTab = screen.getByText('Satisfaction');
    fireEvent.click(satisfactionTab);
    
    await waitFor(() => {
      expect(screen.getByText('Customer Satisfaction')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('should display hourly trends chart', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
    });
    
    const hourlyTab = screen.getByText('Hourly Trends');
    fireEvent.click(hourlyTab);
    
    await waitFor(() => {
      expect(screen.getByText('Hourly Query Distribution')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  it('should display top questions', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
    });
    
    const questionsTab = screen.getByTestId('tab-trigger-questions');
    fireEvent.click(questionsTab);
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Top Questions' })).toBeInTheDocument();
      expect(screen.getByText('How do I reset my password?')).toBeInTheDocument();
      expect(screen.getByText('45 times asked')).toBeInTheDocument();
      expect(screen.getByText('90% satisfied')).toBeInTheDocument();
    });
  });

  it('should handle export data', async () => {
    render(<Analytics />);

    await waitFor(() => {
      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    // Verify export endpoint is called with the expected params
    expect(mockApi.get).toHaveBeenCalledWith('/analytics/detailed-export', { params: { format: 'json' } });
  });

  it('should show filter modal when filter button is clicked', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Filter')).toBeInTheDocument();
    });
    
    const filterButton = screen.getByText('Filter');
    fireEvent.click(filterButton);
    
    expect(screen.getByText('Filter Analytics')).toBeInTheDocument();
    expect(screen.getByText('Date Range')).toBeInTheDocument();
    expect(screen.getByText('Query Type')).toBeInTheDocument();
    expect(screen.getByText('User Type')).toBeInTheDocument();
    expect(screen.getAllByText('Satisfaction').length).toBeGreaterThan(0);
  });

  it('should close filter modal when cancel is clicked', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Filter')).toBeInTheDocument();
    });
    
    const filterButton = screen.getByText('Filter');
    fireEvent.click(filterButton);
    
    expect(screen.getByText('Filter Analytics')).toBeInTheDocument();
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(screen.queryByText('Filter Analytics')).not.toBeInTheDocument();
  });

  it('should apply filters when apply button is clicked', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Filter')).toBeInTheDocument();
    });
    
    const filterButton = screen.getByText('Filter');
    fireEvent.click(filterButton);
    
    expect(screen.getByText('Filter Analytics')).toBeInTheDocument();
    
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);
    
    expect(screen.queryByText('Filter Analytics')).not.toBeInTheDocument();
  });

  it('should handle empty top questions', async () => {
    const emptyTopQuestionsData = {
      data: [],
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/analytics/detailed-top-questions') {
        return Promise.resolve(emptyTopQuestionsData);
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
    });
    
    const questionsTab = screen.getByTestId('tab-trigger-questions');
    fireEvent.click(questionsTab);
    
    await waitFor(() => {
      expect(screen.getByText('No questions found for the selected period')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(<Analytics />);
    
    await waitFor(() => {
      // Should not crash and should show loading states
      expect(screen.getAllByText('...')).toHaveLength(4);
    });
  });

  it('should display satisfaction breakdown', async () => {
    render(<Analytics />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Volume')).toBeInTheDocument();
    });
    
    const satisfactionTab = screen.getByText('Satisfaction');
    fireEvent.click(satisfactionTab);
    
    await waitFor(() => {
      expect(screen.getByText('Customer Satisfaction')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      // Check for satisfaction data in the legend
      expect(screen.getByText(/Satisfied:/)).toBeInTheDocument();
      expect(screen.getByText(/Unsatisfied:/)).toBeInTheDocument();
    });
  });
});
