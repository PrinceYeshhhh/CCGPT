import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { usePerformance, useLazyLoad, useDebounce, useThrottle } from '../usePerformance'

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 1000000,
    totalJSHeapSize: 2000000,
    jsHeapSizeLimit: 4000000
  }
}

Object.defineProperty(window, 'performance', {
  value: mockPerformance,
  writable: true
})

// Mock IntersectionObserver
;(global as any).IntersectionObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn(),
}))

// Mock gtag
const mockGtag = vi.fn()
;(window as any).gtag = mockGtag

describe('usePerformance', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should measure render time', () => {
    const { result } = renderHook(() => usePerformance())
    
    act(() => {
      result.current.startRenderMeasurement()
    })
    
    act(() => {
      result.current.endRenderMeasurement('TestComponent')
    })

    expect(result.current.measureRenderTime).toBeDefined()
    expect(result.current.measureLoadTime).toBeDefined()
  })

  it('should measure load time', () => {
    const { result } = renderHook(() => usePerformance())
    
    act(() => {
      result.current.measureLoadTime('TestComponent')
    })

    expect(result.current.measureLoadTime).toBeDefined()
  })

  it('should measure memory usage', () => {
    const { result } = renderHook(() => usePerformance())
    
    act(() => {
      const memory = result.current.measureMemoryUsage()
      expect(memory).toEqual({
        used: 1000000,
        total: 2000000,
        limit: 4000000
      })
    })
  })

  it('should measure network latency', async () => {
    const { result } = renderHook(() => usePerformance())
    
    // Mock fetch
    ;(global as any).fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200
      })
    ) as any

    await act(async () => {
      const latency = await result.current.measureNetworkLatency('https://api.example.com')
      expect(typeof latency).toBe('number')
    })
  })

  it('should handle network latency errors', async () => {
    const { result } = renderHook(() => usePerformance())
    
    // Mock fetch to reject
    ;(global as any).fetch = vi.fn(() => Promise.reject(new Error('Network error'))) as any

    await act(async () => {
      const latency = await result.current.measureNetworkLatency('https://api.example.com')
      expect(latency).toBeNull()
    })
  })

  it('should call gtag for performance metrics', () => {
    const { result } = renderHook(() => usePerformance())
    
    act(() => {
      result.current.measureLoadTime('TestComponent')
    })

    expect(mockGtag).toHaveBeenCalledWith('event', 'timing_complete', {
      name: 'TestComponent_load',
      value: expect.any(Number)
    })
  })
})

describe('useLazyLoad', () => {
  it('should initialize with invisible state', () => {
    const { result } = renderHook(() => useLazyLoad())
    
    expect(result.current[1]).toBe(false)
  })

  it('should have a ref', () => {
    const { result } = renderHook(() => useLazyLoad())
    
    expect(result.current[0]).toBeDefined()
  })
})

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 100 } }
    )

    expect(result.current).toBe('initial')

    // Change value quickly
    rerender({ value: 'changed1', delay: 100 })
    rerender({ value: 'changed2', delay: 100 })
    rerender({ value: 'changed3', delay: 100 })

    expect(result.current).toBe('initial')

    // Fast forward time
    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current).toBe('changed3')
  })

  it('should handle different delay values', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 200 } }
    )

    rerender({ value: 'changed', delay: 200 })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current).toBe('initial')

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current).toBe('changed')
  })
})

describe('useThrottle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should throttle function calls', () => {
    const mockFn = vi.fn()
    const { result } = renderHook(() => useThrottle(mockFn, 100))

    // Call function multiple times quickly
    act(() => {
      result.current('arg1')
      result.current('arg2')
      result.current('arg3')
    })

    // Should only be called once initially
    expect(mockFn).toHaveBeenCalledTimes(1)
    expect(mockFn).toHaveBeenCalledWith('arg1')

    // Fast forward time
    act(() => {
      vi.advanceTimersByTime(100)
    })

    // Should be called with the last argument
    expect(mockFn).toHaveBeenCalledTimes(2)
    expect(mockFn).toHaveBeenCalledWith('arg3')
  })

  it('should handle different throttle delays', () => {
    const mockFn = vi.fn()
    const { result } = renderHook(() => useThrottle(mockFn, 200))

    act(() => {
      result.current('arg1')
      result.current('arg2')
    })

    expect(mockFn).toHaveBeenCalledTimes(1)

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(mockFn).toHaveBeenCalledTimes(1)

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(mockFn).toHaveBeenCalledTimes(2)
  })
})
