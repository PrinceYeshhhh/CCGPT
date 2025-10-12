import React, { ReactElement } from 'react'
import { render as rtlRender, RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { createMockLocation, createMockHistory } from './test-data'

type ProvidersProps = { children: React.ReactNode }

function Providers({ children }: ProvidersProps) {
  return (
    <MemoryRouter>
      {children}
    </MemoryRouter>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return rtlRender(ui, {
    wrapper: Providers,
    ...options,
  })
}

// Enhanced render function with routing support
export function render(
  ui: ReactElement,
  options: {
    initialRoute?: string
    authValue?: { isAuthenticated: boolean; user?: any; token?: string }
  } & Omit<RenderOptions, 'wrapper'> = {}
) {
  const { initialRoute = '/', authValue, ...renderOptions } = options
  
  // Mock window.location for routing tests
  if (initialRoute) {
    Object.defineProperty(window, 'location', {
      value: createMockLocation(initialRoute),
      writable: true,
    })
  }

  // Mock window.history for navigation tests
  Object.defineProperty(window, 'history', {
    value: createMockHistory(),
    writable: true,
  })

  return rtlRender(ui, {
    wrapper: Providers,
    ...renderOptions,
  })
}

// Mock localStorage utility
export function mockLocalStorage(initialData: Record<string, string> = {}) {
  const store = { ...initialData }
  
  const localStorageMock = {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
    length: Object.keys(store).length,
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  }

  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true,
  })

  return store
}

// Mock fetch utility
export function mockFetch(response: any) {
  const mockResponse = {
    ok: response.ok ?? true,
    status: response.status ?? 200,
    statusText: response.statusText ?? 'OK',
    headers: new Headers(response.headers || {}),
    json: vi.fn().mockResolvedValue(response.json ? response.json() : response.data || {}),
    text: vi.fn().mockResolvedValue(JSON.stringify(response.data || {})),
    blob: vi.fn().mockResolvedValue(new Blob()),
    arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(0)),
    formData: vi.fn().mockResolvedValue(new FormData()),
  }

  global.fetch = vi.fn().mockResolvedValue(mockResponse)
  return mockResponse
}

// Mock window.matchMedia
export function mockMatchMedia(matches: boolean = false) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

// Mock IntersectionObserver
export function mockIntersectionObserver() {
  Object.defineProperty(window, 'IntersectionObserver', {
    writable: true,
    value: vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    })),
  })
}

// Mock ResizeObserver
export function mockResizeObserver() {
  Object.defineProperty(window, 'ResizeObserver', {
    writable: true,
    value: vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    })),
  })
}

// Mock console methods to reduce noise in tests
export function mockConsole() {
  const originalConsole = { ...console }
  
  beforeEach(() => {
    console.error = vi.fn()
    console.warn = vi.fn()
    console.log = vi.fn()
  })

  afterEach(() => {
    Object.assign(console, originalConsole)
  })
}

// Export the standard render function as well
export { render as rtlRender } from '@testing-library/react'
export * from '@testing-library/react'