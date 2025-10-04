/**
 * Test utilities for debugging and timeout management
 */

import { vi } from 'vitest'

// Test timeout configuration
export const TEST_TIMEOUTS = {
  SHORT: 5000,    // 5 seconds
  MEDIUM: 10000,  // 10 seconds
  LONG: 30000,    // 30 seconds
  VERY_LONG: 60000 // 60 seconds
} as const

// Debug logging for tests
export const testLogger = {
  debug: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'test') {
      console.log(`[TEST DEBUG] ${message}`, data || '')
    }
  },
  error: (message: string, error?: any) => {
    if (process.env.NODE_ENV === 'test') {
      console.error(`[TEST ERROR] ${message}`, error || '')
    }
  },
  warn: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'test') {
      console.warn(`[TEST WARN] ${message}`, data || '')
    }
  }
}

// Timeout wrapper for async operations
export const withTimeout = async <T>(
  promise: Promise<T>,
  timeoutMs: number = TEST_TIMEOUTS.MEDIUM,
  errorMessage?: string
): Promise<T> => {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => {
      reject(new Error(errorMessage || `Operation timed out after ${timeoutMs}ms`))
    }, timeoutMs)
  })

  return Promise.race([promise, timeoutPromise])
}

// Mock external services to prevent hanging
export const mockExternalServices = () => {
  // Mock fetch
  global.fetch = vi.fn().mockImplementation((url: string) => {
    testLogger.debug(`Mocking fetch request to: ${url}`)
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    })
  })

  // Mock WebSocket
  global.WebSocket = vi.fn().mockImplementation(() => ({
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: WebSocket.OPEN,
  })) as any

  // Mock IntersectionObserver
  global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))

  // Mock ResizeObserver
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))

  // Mock performance API
  Object.defineProperty(window, 'performance', {
    value: {
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByName: vi.fn(() => []),
      getEntriesByType: vi.fn(() => []),
      clearMarks: vi.fn(),
      clearMeasures: vi.fn(),
    },
    writable: true,
  })

  // Mock requestAnimationFrame
  global.requestAnimationFrame = vi.fn((cb: FrameRequestCallback) => {
    return setTimeout(cb, 16) // ~60fps
  })

  global.cancelAnimationFrame = vi.fn((id: number) => {
    clearTimeout(id)
  })
}

// Test wrapper with debugging
export const withTestDebug = <T extends (...args: any[]) => any>(
  testFn: T,
  testName?: string
): T => {
  return ((...args: any[]) => {
    const name = testName || testFn.name || 'Unknown Test'
    testLogger.debug(`Starting test: ${name}`)
    
    const startTime = Date.now()
    
    try {
      const result = testFn(...args)
      
      // Handle async functions
      if (result && typeof result.then === 'function') {
        return result
          .then((res: any) => {
            const endTime = Date.now()
            testLogger.debug(`Completed test: ${name} in ${endTime - startTime}ms`)
            return res
          })
          .catch((error: any) => {
            const endTime = Date.now()
            testLogger.error(`Failed test: ${name} after ${endTime - startTime}ms`, error)
            throw error
          })
      } else {
        const endTime = Date.now()
        testLogger.debug(`Completed test: ${name} in ${endTime - startTime}ms`)
        return result
      }
    } catch (error) {
      const endTime = Date.now()
      testLogger.error(`Failed test: ${name} after ${endTime - startTime}ms`, error)
      throw error
    }
  }) as T
}

// Skip problematic tests
export const skipTest = (reason: string) => {
  testLogger.warn(`Skipping test: ${reason}`)
  return vi.fn().mockImplementation(() => {
    throw new Error(`Test skipped: ${reason}`)
  })
}

// Mark slow tests
export const slowTest = (timeoutMs: number = TEST_TIMEOUTS.LONG) => {
  return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
    const originalMethod = descriptor.value
    descriptor.value = withTimeout(originalMethod, timeoutMs, `Slow test timed out after ${timeoutMs}ms`)
    return descriptor
  }
}

// Check if external services are available
export const checkExternalServices = () => {
  const services = {
    'API': process.env.VITE_API_URL || 'http://localhost:8000',
    'WebSocket': 'ws://localhost:8000/ws',
  }

  Object.entries(services).forEach(([name, url]) => {
    testLogger.debug(`Checking ${name} at ${url}`)
  })
}
