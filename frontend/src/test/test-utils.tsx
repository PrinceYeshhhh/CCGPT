import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ThemeProvider } from '../contexts/ThemeContext'

// Mock user data for testing
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  name: 'Test User',
  plan: 'pro',
  isActive: true,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
}

// Mock auth context value
export const mockAuthValue = {
  user: mockUser,
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn(),
  refreshUser: vi.fn(),
}

// Mock theme context value
export const mockThemeValue = {
  theme: 'light',
  toggleTheme: vi.fn(),
  setTheme: vi.fn(),
}

// Custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authValue?: Partial<typeof mockAuthValue>
  themeValue?: Partial<typeof mockThemeValue>
  initialRoute?: string
}

const AllTheProviders = ({ 
  children, 
  authValue = mockAuthValue, 
  themeValue = mockThemeValue 
}: { 
  children: React.ReactNode
  authValue?: Partial<typeof mockAuthValue>
  themeValue?: Partial<typeof mockThemeValue>
}) => {
  const mergedAuthValue = { ...mockAuthValue, ...authValue }
  const mergedThemeValue = { ...mockThemeValue, ...themeValue }

  return (
      <BrowserRouter>
      <AuthProvider value={mergedAuthValue}>
        <ThemeProvider value={mergedThemeValue}>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { authValue, themeValue, initialRoute, ...renderOptions } = options

  // Set initial route if provided
  if (initialRoute) {
    window.history.pushState({}, '', initialRoute)
  }

  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders authValue={authValue} themeValue={themeValue}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  })
}

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Mock API responses
export const mockApiResponses = {
  success: (data: any) => ({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  }),
  error: (status: number = 500, message: string = 'Internal Server Error') => ({
    ok: false,
    status,
    json: () => Promise.resolve({ error: message }),
  }),
  unauthorized: () => ({
    ok: false,
    status: 401,
    json: () => Promise.resolve({ error: 'Unauthorized' }),
  }),
  forbidden: () => ({
    ok: false,
    status: 403,
    json: () => Promise.resolve({ error: 'Forbidden' }),
  }),
  notFound: () => ({
    ok: false,
    status: 404,
    json: () => Promise.resolve({ error: 'Not Found' }),
  }),
}

// Mock fetch with different response types
export const mockFetch = (response: any) => {
  global.fetch = vi.fn(() => Promise.resolve(response))
}

// Mock fetch with error
export const mockFetchError = (error: Error) => {
  global.fetch = vi.fn(() => Promise.reject(error))
}

// Mock localStorage
export const mockLocalStorage = (data: Record<string, string> = {}) => {
  const store = { ...data }
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
  }
  Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  return store
}

// Mock sessionStorage
export const mockSessionStorage = (data: Record<string, string> = {}) => {
  const store = { ...data }
  const sessionStorageMock = {
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
  }
  Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock })
  return store
}

// Wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0))

// Mock file for testing file uploads
export const createMockFile = (name: string, type: string, content: string = 'test content') => {
  const file = new File([content], name, { type })
  return file
}

// Mock form data
export const createMockFormData = (data: Record<string, any>) => {
  const formData = new FormData()
  Object.entries(data).forEach(([key, value]) => {
    formData.append(key, value)
  })
  return formData
}

// Mock intersection observer
export const mockIntersectionObserver = (isIntersecting: boolean = true) => {
  const mockObserver = vi.fn()
  mockObserver.mockReturnValue({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  })
  global.IntersectionObserver = mockObserver

  // Mock the callback to immediately call with intersection
  if (isIntersecting) {
    setTimeout(() => {
      const callback = mockObserver.mock.calls[0]?.[0]
      if (callback) {
        callback([{ isIntersecting: true, intersectionRatio: 1 }])
      }
    }, 0)
  }

  return mockObserver
}

// Mock resize observer
export const mockResizeObserver = () => {
  const mockObserver = vi.fn()
  mockObserver.mockReturnValue({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  })
  global.ResizeObserver = mockObserver
  return mockObserver
}

// Mock window.matchMedia
export const mockMatchMedia = (matches: boolean = false) => {
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

// Mock clipboard
export const mockClipboard = (text: string = '') => {
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: vi.fn().mockResolvedValue(undefined),
      readText: vi.fn().mockResolvedValue(text),
    },
    writable: true,
  })
}

// Mock URL.createObjectURL
export const mockCreateObjectURL = (url: string = 'mock-url') => {
  Object.defineProperty(URL, 'createObjectURL', {
    value: vi.fn(() => url),
    writable: true,
  })
}

// Mock URL.revokeObjectURL
export const mockRevokeObjectURL = () => {
  Object.defineProperty(URL, 'revokeObjectURL', {
    value: vi.fn(),
    writable: true,
  })
}

// Mock performance.now
export const mockPerformanceNow = (time: number = Date.now()) => {
  Object.defineProperty(window.performance, 'now', {
    value: vi.fn(() => time),
    writable: true,
  })
}

// Mock getBoundingClientRect
export const mockGetBoundingClientRect = (rect: Partial<DOMRect> = {}) => {
  const defaultRect = {
    width: 120,
    height: 120,
    top: 0,
    left: 0,
    bottom: 0,
    right: 0,
    x: 0,
    y: 0,
    toJSON: vi.fn(),
  }
  
  Element.prototype.getBoundingClientRect = vi.fn(() => ({
    ...defaultRect,
    ...rect,
  }))
}

// Mock scrollTo
export const mockScrollTo = () => {
  Object.defineProperty(window, 'scrollTo', {
    value: vi.fn(),
    writable: true,
  })
}

// Mock alert
export const mockAlert = () => {
  Object.defineProperty(window, 'alert', {
    value: vi.fn(),
    writable: true,
  })
}

// Mock confirm
export const mockConfirm = (returnValue: boolean = true) => {
  Object.defineProperty(window, 'confirm', {
    value: vi.fn(() => returnValue),
    writable: true,
  })
}

// Mock prompt
export const mockPrompt = (returnValue: string = '') => {
  Object.defineProperty(window, 'prompt', {
    value: vi.fn(() => returnValue),
    writable: true,
  })
}

// Mock crypto.randomUUID
export const mockRandomUUID = (uuid: string = 'mock-uuid') => {
  Object.defineProperty(global, 'crypto', {
    value: {
      randomUUID: vi.fn(() => uuid),
      getRandomValues: vi.fn((arr) => arr),
    },
    writable: true,
  })
}

// Mock FileReader
export const mockFileReader = (result: string = 'test content') => {
  const mockReader = {
    readAsText: vi.fn(),
    readAsDataURL: vi.fn(),
    readAsArrayBuffer: vi.fn(),
    result,
    error: null,
    onload: null,
    onerror: null,
    onabort: null,
    onloadend: null,
    onloadstart: null,
    onprogress: null,
    abort: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }
  
  global.FileReader = vi.fn(() => mockReader)
  return mockReader
}

// Mock MutationObserver
export const mockMutationObserver = () => {
  const mockObserver = vi.fn()
  mockObserver.mockReturnValue({
    observe: vi.fn(),
    disconnect: vi.fn(),
    takeRecords: vi.fn(() => []),
  })
  global.MutationObserver = mockObserver
  return mockObserver
}

// Mock AbortController
export const mockAbortController = () => {
  const mockController = {
    abort: vi.fn(),
    signal: {
      aborted: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    },
  }
  global.AbortController = vi.fn(() => mockController)
  return mockController
}

// Test data factories
export const createMockUser = (overrides: Partial<typeof mockUser> = {}) => ({
  ...mockUser,
  ...overrides,
})

export const createMockAuthValue = (overrides: Partial<typeof mockAuthValue> = {}) => ({
  ...mockAuthValue,
  ...overrides,
})

export const createMockThemeValue = (overrides: Partial<typeof mockThemeValue> = {}) => ({
  ...mockThemeValue,
  ...overrides,
})

// Common test assertions
export const expectElementToBeInDocument = (element: HTMLElement | null) => {
  expect(element).toBeInTheDocument()
}

export const expectElementNotToBeInDocument = (element: HTMLElement | null) => {
  expect(element).not.toBeInTheDocument()
}

export const expectElementToHaveTextContent = (element: HTMLElement | null, text: string) => {
  expect(element).toHaveTextContent(text)
}

export const expectElementToHaveClass = (element: HTMLElement | null, className: string) => {
  expect(element).toHaveClass(className)
}

export const expectElementToHaveAttribute = (element: HTMLElement | null, attribute: string, value?: string) => {
  expect(element).toHaveAttribute(attribute, value)
}

// Import vi for the mocks
import { vi } from 'vitest'