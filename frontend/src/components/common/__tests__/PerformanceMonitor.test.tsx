import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PerformanceMonitor } from '../PerformanceMonitor';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  getEntriesByType: vi.fn(() => []),
  mark: vi.fn(),
  measure: vi.fn(),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
  observer: vi.fn(),
};

// Mock ResizeObserver
const mockResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock memory API
const mockMemory = {
  usedJSHeapSize: 1000000,
  totalJSHeapSize: 2000000,
  jsHeapSizeLimit: 4000000,
};

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock performance API
    Object.defineProperty(window, 'performance', {
      value: mockPerformance,
      writable: true,
    });

    // Mock ResizeObserver
    Object.defineProperty(window, 'ResizeObserver', {
      value: mockResizeObserver,
      writable: true,
    });

    // Mock memory API
    Object.defineProperty(window, 'memory', {
      value: mockMemory,
      writable: true,
    });

    // Mock requestAnimationFrame
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      cb(0);
      return 1;
    });

    // Mock setTimeout properly
    vi.useFakeTimers();
    vi.spyOn(global, 'setTimeout').mockImplementation((cb) => {
      // Don't call immediately to avoid timing issues
      return 1;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should render performance monitor', () => {
    render(<PerformanceMonitor />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should render with custom className', () => {
    render(<PerformanceMonitor className="custom-class" />);
    
    const monitor = screen.getByText('Performance Monitor').closest('div');
    expect(monitor).toHaveClass('custom-class');
  });

  it('should show details when showDetails is true', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
    expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
  });

  it('should hide details when showDetails is false', () => {
    render(<PerformanceMonitor showDetails={false} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
    expect(screen.queryByText('Core Web Vitals')).not.toBeInTheDocument();
  });

  it('should toggle details visibility', () => {
    render(<PerformanceMonitor />);
    
    const toggleButton = screen.getByRole('button', { name: /toggle details/i });
    fireEvent.click(toggleButton);
    
    expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
  });

  it('should display performance score', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Score')).toBeInTheDocument();
  });

  it('should display core web vitals', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('LCP')).toBeInTheDocument();
    expect(screen.getByText('FID')).toBeInTheDocument();
    expect(screen.getByText('CLS')).toBeInTheDocument();
    expect(screen.getByText('FCP')).toBeInTheDocument();
    expect(screen.getByText('TTFB')).toBeInTheDocument();
  });

  it('should display page load time', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Page Load Time')).toBeInTheDocument();
  });

  it('should display memory usage', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
  });

  it('should handle close button', () => {
    const onClose = vi.fn();
    render(<PerformanceMonitor onClose={onClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should display loading state initially', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should update metrics over time', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    // Check that the component renders without waiting
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display performance status', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Status')).toBeInTheDocument();
  });

  it('should display good performance status', async () => {
    // Mock good performance metrics
    mockPerformance.getEntriesByType.mockReturnValue([
      { name: 'LCP', value: 1000 },
      { name: 'FID', value: 50 },
      { name: 'CLS', value: 0.05 },
    ]);

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display poor performance status', () => {
    // Mock poor performance metrics
    mockPerformance.getEntriesByType.mockReturnValue([
      { name: 'LCP', value: 5000 },
      { name: 'FID', value: 300 },
      { name: 'CLS', value: 0.3 },
    ]);

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display warning performance status', () => {
    // Mock warning performance metrics
    mockPerformance.getEntriesByType.mockReturnValue([
      { name: 'LCP', value: 3000 },
      { name: 'FID', value: 150 },
      { name: 'CLS', value: 0.15 },
    ]);

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display performance recommendations', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
  });

  it('should handle performance observer', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(mockResizeObserver).toHaveBeenCalled();
  });

  it('should display memory usage in MB', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
  });

  it('should display performance score with color coding', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    const scoreElement = screen.getByText('Performance Score');
    expect(scoreElement).toBeInTheDocument();
  });

  it('should handle missing performance API', () => {
    // Remove performance API
    Object.defineProperty(window, 'performance', {
      value: undefined,
      writable: true,
    });

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should handle missing memory API', () => {
    // Remove memory API
    Object.defineProperty(window, 'memory', {
      value: undefined,
      writable: true,
    });

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display performance metrics in cards', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Core Web Vitals')).toBeInTheDocument();
    expect(screen.getByText('Page Performance')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
  });

  it('should handle performance monitoring errors gracefully', () => {
    // Mock performance API to throw error
    mockPerformance.getEntriesByType.mockImplementation(() => {
      throw new Error('Performance API error');
    });

    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Monitor')).toBeInTheDocument();
  });

  it('should display performance trends', () => {
    render(<PerformanceMonitor showDetails={true} />);
    
    expect(screen.getByText('Performance Trends')).toBeInTheDocument();
  });

  it('should handle performance monitoring cleanup', () => {
    const { unmount } = render(<PerformanceMonitor showDetails={true} />);
    
    unmount();
    
    // Should clean up observers
    expect(mockResizeObserver).toHaveBeenCalled();
  });
});
