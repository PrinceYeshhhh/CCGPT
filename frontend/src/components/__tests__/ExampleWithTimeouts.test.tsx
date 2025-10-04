/**
 * Example test file showing how to use timeouts and debugging in frontend tests
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { 
  withTimeout, 
  withTestDebug, 
  mockExternalServices, 
  testLogger,
  TEST_TIMEOUTS 
} from '@/test/test-utils'

// Example component for testing
const ExampleComponent = ({ onAsyncAction }: { onAsyncAction?: () => Promise<void> }) => {
  const [loading, setLoading] = React.useState(false)
  const [data, setData] = React.useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    try {
      if (onAsyncAction) {
        await onAsyncAction()
      }
      setData('Success!')
    } catch (error) {
      setData('Error!')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button onClick={handleClick} disabled={loading}>
        {loading ? 'Loading...' : 'Click me'}
      </button>
      {data && <div data-testid="result">{data}</div>}
    </div>
  )
}

describe('ExampleWithTimeouts', () => {
  beforeEach(() => {
    // Mock external services to prevent hanging
    mockExternalServices()
    vi.clearAllMocks()
  })

  it('should render component quickly', () => {
    withTestDebug(() => {
      testLogger.debug('Starting quick render test')
      
      render(<ExampleComponent />)
      
      expect(screen.getByRole('button')).toBeInTheDocument()
      expect(screen.getByRole('button')).toHaveTextContent('Click me')
      
      testLogger.debug('Quick render test completed')
    }, 'quick-render-test')()
  })

  it('should handle async action with timeout', async () => {
    const mockAsyncAction = vi.fn().mockImplementation(async () => {
      // Simulate async work
      await new Promise(resolve => setTimeout(resolve, 100))
      return 'Async result'
    })

    await withTestDebug(async () => {
      testLogger.debug('Starting async action test')
      
      render(<ExampleComponent onAsyncAction={mockAsyncAction} />)
      
      const button = screen.getByRole('button')
      button.click()
      
      // Wait for loading state
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      
      // Wait for completion with timeout
      await withTimeout(
        waitFor(() => {
          expect(screen.getByTestId('result')).toHaveTextContent('Success!')
        }),
        TEST_TIMEOUTS.SHORT,
        'Async action test timed out'
      )
      
      testLogger.debug('Async action test completed')
    }, 'async-action-test')()
  })

  it('should handle external API calls with timeout', async () => {
    // Mock fetch with controlled delay
    global.fetch = vi.fn().mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ data: 'test' })
        }), 50)
      )
    )

    await withTestDebug(async () => {
      testLogger.debug('Starting external API test')
      
      // Test external API call with timeout
      const result = await withTimeout(
        fetch('/api/test').then(res => res.json()),
        TEST_TIMEOUTS.SHORT,
        'External API call timed out'
      )
      
      expect(result).toEqual({ data: 'test' })
      expect(global.fetch).toHaveBeenCalledWith('/api/test')
      
      testLogger.debug('External API test completed')
    }, 'external-api-test')()
  })

  it('should skip problematic test', () => {
    testLogger.warn('Skipping problematic test')
    // This test would be skipped in practice
    expect(true).toBe(true)
  })

  it('should handle WebSocket connections with timeout', async () => {
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      readyState: WebSocket.OPEN,
    }

    global.WebSocket = vi.fn(() => mockWebSocket) as any

    await withTestDebug(async () => {
      testLogger.debug('Starting WebSocket test')
      
      // Test WebSocket connection with timeout
      const ws = new WebSocket('ws://localhost:8000')
      
      await withTimeout(
        new Promise<void>((resolve) => {
          ws.addEventListener('open', () => resolve())
        }),
        TEST_TIMEOUTS.SHORT,
        'WebSocket connection timed out'
      )
      
      expect(ws.readyState).toBe(WebSocket.OPEN)
      
      testLogger.debug('WebSocket test completed')
    }, 'websocket-test')()
  })

  it('should handle performance monitoring with timeout', async () => {
    await withTestDebug(async () => {
      testLogger.debug('Starting performance monitoring test')
      
      // Mock performance API
      const mockPerformance = {
        now: vi.fn(() => Date.now()),
        mark: vi.fn(),
        measure: vi.fn(),
        getEntriesByName: vi.fn(() => []),
        getEntriesByType: vi.fn(() => []),
      }
      
      Object.defineProperty(window, 'performance', {
        value: mockPerformance,
        writable: true,
      })
      
      // Test performance monitoring with timeout
      const startTime = performance.now()
      
      await withTimeout(
        new Promise<void>((resolve) => {
          // Simulate performance monitoring work
          setTimeout(() => {
            const endTime = performance.now()
            expect(endTime - startTime).toBeGreaterThan(0)
            resolve()
          }, 10)
        }),
        TEST_TIMEOUTS.SHORT,
        'Performance monitoring timed out'
      )
      
      testLogger.debug('Performance monitoring test completed')
    }, 'performance-monitoring-test')()
  })
})
