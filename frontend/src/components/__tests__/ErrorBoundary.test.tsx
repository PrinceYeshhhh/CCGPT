import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import ErrorBoundary from '../ErrorBoundary'

// Mock component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error
  beforeAll(() => {
    console.error = vi.fn()
  })

  afterAll(() => {
    console.error = originalError
  })

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  it('renders error UI when there is an error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
    expect(screen.getByText('Go Home')).toBeInTheDocument()
  })

  it('shows error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Error Details:')).toBeInTheDocument()
    expect(screen.getByText(/Test error/)).toBeInTheDocument()

    process.env.NODE_ENV = originalEnv
  })

  it('hides error details in production mode', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.queryByText('Error Details:')).not.toBeInTheDocument()

    process.env.NODE_ENV = originalEnv
  })

  it('calls retry function when Try Again is clicked', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    // Initially should show error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    
    const retryButton = screen.getByText('Try Again')
    fireEvent.click(retryButton)
    
    // After retry, re-render with shouldThrow=false to simulate successful retry
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )
    
    // After retry, the error should be cleared and children should render
    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  it('navigates to home when Go Home is clicked', () => {
    // Mock window.location.href
    delete (window as any).location
    window.location = { href: '' } as any

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    const homeButton = screen.getByText('Go Home')
    fireEvent.click(homeButton)
    
    expect(window.location.href).toBe('/')
  })

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Custom error message')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })
})
