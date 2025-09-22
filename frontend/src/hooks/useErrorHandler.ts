import { useCallback } from 'react'
import toast from 'react-hot-toast'

interface ErrorHandlerOptions {
  showToast?: boolean
  logError?: boolean
  fallbackMessage?: string
}

export const useErrorHandler = () => {
  const handleError = useCallback((
    error: Error | unknown,
    options: ErrorHandlerOptions = {}
  ) => {
    const {
      showToast = true,
      logError = true,
      fallbackMessage = 'An unexpected error occurred'
    } = options

    // Log error to console in development
    if (logError && process.env.NODE_ENV === 'development') {
      console.error('Error caught by useErrorHandler:', error)
    }

    // Extract error message
    let errorMessage = fallbackMessage
    if (error instanceof Error) {
      errorMessage = error.message
    } else if (typeof error === 'string') {
      errorMessage = error
    }

    // Show toast notification
    if (showToast) {
      toast.error(errorMessage, {
        duration: 5000,
        position: 'top-right'
      })
    }

    // Log to external monitoring service (if available)
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: errorMessage,
        fatal: false
      })
    }
  }, [])

  const handleAsyncError = useCallback(async (
    asyncFn: () => Promise<any>,
    options: ErrorHandlerOptions = {}
  ) => {
    try {
      return await asyncFn()
    } catch (error) {
      handleError(error, options)
      throw error // Re-throw to allow calling code to handle if needed
    }
  }, [handleError])

  return {
    handleError,
    handleAsyncError
  }
}

// Global error handler for unhandled promise rejections
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    
    // Show toast for unhandled promise rejections
    toast.error('An unexpected error occurred. Please try again.')
    
    // Prevent the default browser behavior
    event.preventDefault()
  })
}

// Global error handler for uncaught errors
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error)
    
    // Show toast for uncaught errors
    toast.error('An unexpected error occurred. Please refresh the page.')
  })
}
