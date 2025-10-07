import '@testing-library/jest-dom'
import { vi, afterEach, afterAll, beforeEach, beforeAll } from 'vitest'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

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

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn(cb => setTimeout(cb, 0))
global.cancelAnimationFrame = vi.fn(id => clearTimeout(id))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
})

// Ensure timers and mocks don't keep the process alive between tests
beforeEach(() => {
  vi.useRealTimers()
})

// Reduce console.error noise from React error boundaries in tests to avoid memory bloat
const originalConsoleError = console.error
beforeAll(() => {
  console.error = ((...args: any[]) => {
    const first = args[0]
    if (typeof first === 'string') {
      if (
        first.includes('The above error occurred') ||
        first.includes('ErrorBoundary caught an error') ||
        first.startsWith('Error: Boom')
      ) {
        return
      }
    }
    // Fallback to original
    // eslint-disable-next-line prefer-spread
    return (originalConsoleError as any).apply(console, args)
  }) as any
})

afterEach(() => {
  vi.clearAllTimers()
  vi.clearAllMocks()
})

afterAll(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  console.error = originalConsoleError
})
