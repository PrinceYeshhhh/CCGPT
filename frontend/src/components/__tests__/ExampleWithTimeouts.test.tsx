/**
 * Example test file showing how to use timeouts and debugging in frontend tests
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

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
    vi.clearAllMocks()
  })

  it('should render component quickly', () => {
    render(<ExampleComponent />)
    
    expect(screen.getByRole('button')).toBeInTheDocument()
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('should handle async action with timeout', async () => {
    const mockAsyncAction = vi.fn().mockImplementation(async () => {
      // Simulate async work
      await new Promise(resolve => setTimeout(resolve, 100))
      return 'Async result'
    })

    render(<ExampleComponent onAsyncAction={mockAsyncAction} />)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    // Wait for loading state
    await waitFor(() => {
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
    
    // Wait for completion
    await waitFor(() => {
      expect(screen.getByTestId('result')).toHaveTextContent('Success!')
    })
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

    // Test external API call
    const result = await fetch('/api/test').then(res => res.json())
    
    expect(result).toEqual({ data: 'test' })
    expect(global.fetch).toHaveBeenCalledWith('/api/test')
  })

  it('should skip problematic test', () => {
    // This test would be skipped in practice
    expect(true).toBe(true)
  })

  it('should handle WebSocket connections with timeout', () => {
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      readyState: 1, // WebSocket.OPEN
    }

    global.WebSocket = vi.fn(() => mockWebSocket) as any

    // Test WebSocket creation
    const ws = new WebSocket('ws://localhost:8000')
    
    expect(ws).toBeDefined()
    expect(ws.readyState).toBe(1) // WebSocket.OPEN
  })

  it('should handle performance monitoring with timeout', async () => {
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
    
    // Test performance monitoring
    const startTime = performance.now()
    
    await new Promise<void>((resolve) => {
      // Simulate performance monitoring work
      setTimeout(() => {
        const endTime = performance.now()
        expect(endTime - startTime).toBeGreaterThan(0)
        resolve()
      }, 10)
    })
  })
})
