/**
 * Unit tests for usePerformance hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePerformance } from '../usePerformance';

// Mock performance API
const mockPerformance = {
  now: vi.fn(),
  mark: vi.fn(),
  measure: vi.fn(),
  getEntriesByName: vi.fn(),
  getEntriesByType: vi.fn(),
  clearMarks: vi.fn(),
  clearMeasures: vi.fn(),
};

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true,
});

// Mock requestAnimationFrame
const mockRequestAnimationFrame = vi.fn();
Object.defineProperty(window, 'requestAnimationFrame', {
  value: mockRequestAnimationFrame,
  writable: true,
});

// Mock setTimeout
const mockSetTimeout = vi.fn();
Object.defineProperty(global, 'setTimeout', {
  value: mockSetTimeout,
  writable: true,
});

describe('usePerformance Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPerformance.now.mockReturnValue(1000);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes with default values', () => {
    const { result } = renderHook(() => usePerformance());
    
    expect(result.current.metrics).toEqual({
      renderTime: 0,
      memoryUsage: 0,
      networkLatency: 0,
      errorCount: 0,
    });
    expect(result.current.isMonitoring).toBe(false);
  });

  it('starts monitoring when startMonitoring is called', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    expect(result.current.isMonitoring).toBe(true);
  });

  it('stops monitoring when stopMonitoring is called', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    expect(result.current.isMonitoring).toBe(true);

    act(() => {
      result.current.stopMonitoring();
    });

    expect(result.current.isMonitoring).toBe(false);
  });

  it('measures render time correctly', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    // Simulate render start
    act(() => {
      result.current.markRenderStart('test-component');
    });

    // Simulate render end
    mockPerformance.now.mockReturnValue(1500);
    act(() => {
      result.current.markRenderEnd('test-component');
    });

    expect(result.current.metrics.renderTime).toBe(500);
  });

  it('tracks memory usage', () => {
    const { result } = renderHook(() => usePerformance());

    // Mock memory API
    Object.defineProperty(performance, 'memory', {
      value: {
        usedJSHeapSize: 1000000,
        totalJSHeapSize: 2000000,
        jsHeapSizeLimit: 4000000,
      },
      writable: true,
    });

    act(() => {
      result.current.startMonitoring();
    });

    act(() => {
      result.current.updateMemoryUsage();
    });

    expect(result.current.metrics.memoryUsage).toBe(1000000);
  });

  it('tracks network latency', async () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    
    await act(async () => {
      await result.current.measureNetworkLatency('/api/test');
    });
    
    expect(result.current.metrics.networkLatency).toBeGreaterThan(0);
  });

  it('handles network errors gracefully', async () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // Mock fetch to reject
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
    
    await act(async () => {
      await result.current.measureNetworkLatency('/api/test');
    });

    expect(result.current.metrics.errorCount).toBe(1);
  });

  it('tracks error count', () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    act(() => {
      result.current.incrementErrorCount();
    });

    expect(result.current.metrics.errorCount).toBe(1);

    act(() => {
      result.current.incrementErrorCount();
    });

    expect(result.current.metrics.errorCount).toBe(2);
  });

  it('resets metrics when resetMetrics is called', () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // Set some metrics
    act(() => {
      result.current.markRenderStart('test');
      result.current.markRenderEnd('test');
      result.current.incrementErrorCount();
    });

    act(() => {
      result.current.resetMetrics();
    });

    expect(result.current.metrics).toEqual({
      renderTime: 0,
      memoryUsage: 0,
      networkLatency: 0,
      errorCount: 0,
      });
    });
    
  it('handles multiple render measurements', () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // First render
    act(() => {
      result.current.markRenderStart('component1');
    });
    mockPerformance.now.mockReturnValue(1200);
    act(() => {
      result.current.markRenderEnd('component1');
    });

    // Second render
    act(() => {
      result.current.markRenderStart('component2');
    });
    mockPerformance.now.mockReturnValue(1500);
    act(() => {
      result.current.markRenderEnd('component2');
    });

    // Should track the latest render time
    expect(result.current.metrics.renderTime).toBe(300);
  });

  it('handles missing performance API gracefully', () => {
    // Remove performance API
    Object.defineProperty(window, 'performance', {
      value: undefined,
      writable: true,
    });
    
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // Should not throw error
    expect(result.current.isMonitoring).toBe(true);
  });

  it('handles missing memory API gracefully', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    // Remove memory API
    Object.defineProperty(performance, 'memory', {
      value: undefined,
      writable: true,
    });

    act(() => {
      result.current.updateMemoryUsage();
    });

    // Should not throw error
    expect(result.current.metrics.memoryUsage).toBe(0);
  });

  it('provides performance report', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    // Set some metrics
    act(() => {
      result.current.markRenderStart('test');
      result.current.markRenderEnd('test');
      result.current.incrementErrorCount();
    });

    const report = result.current.getPerformanceReport();

    expect(report).toHaveProperty('metrics');
    expect(report).toHaveProperty('timestamp');
    expect(report).toHaveProperty('isMonitoring');
    expect(report.metrics.renderTime).toBeGreaterThan(0);
  });

  it('handles concurrent monitoring sessions', () => {
    const { result } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    // Start another monitoring session
    act(() => {
      result.current.startMonitoring();
    });

    // Should still be monitoring
    expect(result.current.isMonitoring).toBe(true);

    // Stop monitoring
    act(() => {
      result.current.stopMonitoring();
    });

    expect(result.current.isMonitoring).toBe(false);
  });

  it('cleans up on unmount', () => {
    const { result, unmount } = renderHook(() => usePerformance());
    
    act(() => {
      result.current.startMonitoring();
    });

    expect(result.current.isMonitoring).toBe(true);

    unmount();

    // Should clean up monitoring
    expect(result.current.isMonitoring).toBe(false);
  });

  it('handles rapid start/stop cycles', () => {
    const { result } = renderHook(() => usePerformance());

    // Rapid start/stop cycles
    for (let i = 0; i < 10; i++) {
      act(() => {
        result.current.startMonitoring();
      });
      act(() => {
        result.current.stopMonitoring();
      });
    }

    expect(result.current.isMonitoring).toBe(false);
  });

  it('tracks performance marks correctly', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    act(() => {
      result.current.markRenderStart('test-component');
    });

    expect(mockPerformance.mark).toHaveBeenCalledWith('render-start-test-component');

    act(() => {
      result.current.markRenderEnd('test-component');
    });

    expect(mockPerformance.mark).toHaveBeenCalledWith('render-end-test-component');
  });

  it('measures performance between marks', () => {
    const { result } = renderHook(() => usePerformance());

    act(() => {
      result.current.startMonitoring();
    });

    act(() => {
      result.current.markRenderStart('test-component');
    });

    act(() => {
      result.current.markRenderEnd('test-component');
    });

    expect(mockPerformance.measure).toHaveBeenCalledWith(
      'render-test-component',
      'render-start-test-component',
      'render-end-test-component'
    );
  });
});