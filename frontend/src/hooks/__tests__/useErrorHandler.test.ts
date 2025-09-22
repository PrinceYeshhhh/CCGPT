import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useErrorHandler } from '../useErrorHandler'

// Mock toast
vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn()
  },
  error: vi.fn()
}))

// Mock gtag
const mockGtag = vi.fn()
;(window as any).gtag = mockGtag

describe('useErrorHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should handle error with default options', () => {
    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error)
    })

    expect(result.current.handleError).toBeDefined()
  })

  it('should handle error with custom options', () => {
    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error, {
        showToast: false,
        logError: false,
        fallbackMessage: 'Custom error message'
      })
    })

    expect(result.current.handleError).toBeDefined()
  })

  it('should handle string errors', () => {
    const { result } = renderHook(() => useErrorHandler())
    const error = 'String error message'

    act(() => {
      result.current.handleError(error)
    })

    expect(result.current.handleError).toBeDefined()
  })

  it('should handle async errors', async () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const asyncFunction = async () => {
      throw new Error('Async error')
    }

    await act(async () => {
      try {
        await result.current.handleAsyncError(asyncFunction)
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.handleAsyncError).toBeDefined()
  })

  it('should handle successful async operations', async () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const asyncFunction = async () => {
      return 'success'
    }

    let returnValue: string | undefined

    await act(async () => {
      returnValue = await result.current.handleAsyncError(asyncFunction)
    })

    expect(returnValue).toBe('success')
  })

  it('should log errors in development mode', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'
    
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error, { logError: true })
    })

    expect(consoleSpy).toHaveBeenCalledWith('Error caught by useErrorHandler:', error)
    
    consoleSpy.mockRestore()
    process.env.NODE_ENV = originalEnv
  })

  it('should not log errors in production mode', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error, { logError: true })
    })

    expect(consoleSpy).not.toHaveBeenCalled()
    
    consoleSpy.mockRestore()
    process.env.NODE_ENV = originalEnv
  })

  it('should call gtag when available', () => {
    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error)
    })

    expect(mockGtag).toHaveBeenCalledWith('event', 'exception', {
      description: 'Test error',
      fatal: false
    })
  })

  it('should not call gtag when not available', () => {
    const originalGtag = (window as any).gtag
    delete (window as any).gtag

    const { result } = renderHook(() => useErrorHandler())
    const error = new Error('Test error')

    act(() => {
      result.current.handleError(error)
    })

    // Should not throw
    expect(result.current.handleError).toBeDefined()

    // Restore gtag
    ;(window as any).gtag = originalGtag
  })
})
