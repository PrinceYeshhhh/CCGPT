import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'
import { vi, afterEach, afterAll, beforeEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'

// Ensure a root container exists for React 18 createRoot during tests
beforeAll(() => {
  const existing = document.getElementById('root')
  if (!existing) {
    const root = document.createElement('div')
    root.setAttribute('id', 'root')
    document.body.appendChild(root)
  }
})

// Use legacyRoot to align @testing-library/react with React 18 in tests
configure({ legacyRoot: true })

// Provide a default mock for AuthContext hook to avoid module-not-found during tests
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: false })
}))

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

// Mock fetch
global.fetch = vi.fn()

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  value: vi.fn(() => 'mock-url'),
  writable: true,
})

// Mock URL.revokeObjectURL
Object.defineProperty(URL, 'revokeObjectURL', {
  value: vi.fn(),
  writable: true,
})

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
    readText: vi.fn().mockResolvedValue(''),
  },
  writable: true,
})

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: vi.fn(),
    replace: vi.fn(),
    reload: vi.fn(),
  },
  writable: true,
})

// Mock window.history
Object.defineProperty(window, 'history', {
  value: {
    pushState: vi.fn(),
    replaceState: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  },
  writable: true,
})

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
})

// Mock window.getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: vi.fn(() => ({
    getPropertyValue: vi.fn(() => ''),
  })),
  writable: true,
})

// Mock window.getBoundingClientRect
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  width: 120,
  height: 120,
  top: 0,
  left: 0,
  bottom: 0,
  right: 0,
  x: 0,
  y: 0,
  toJSON: vi.fn(),
}))

// Mock window.alert
Object.defineProperty(window, 'alert', {
  value: vi.fn(),
  writable: true,
})

// Mock window.confirm
Object.defineProperty(window, 'confirm', {
  value: vi.fn(() => true),
  writable: true,
})

// Mock window.prompt
Object.defineProperty(window, 'prompt', {
  value: vi.fn(() => ''),
  writable: true,
})

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    getEntriesByType: vi.fn(() => []),
    mark: vi.fn(),
    measure: vi.fn(),
    clearMarks: vi.fn(),
    clearMeasures: vi.fn(),
  },
  writable: true,
})

// Mock MutationObserver
global.MutationObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => []),
}))

// Mock FileReader
global.FileReader = vi.fn().mockImplementation(() => ({
  readAsText: vi.fn(),
  readAsDataURL: vi.fn(),
  readAsArrayBuffer: vi.fn(),
  result: '',
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
}))

// Minimal class shims to match web API behavior more closely
class BlobShim {
  size: number
  type: string
  constructor(parts: any[] = [], options: any = {}) {
    this.size = Array.isArray(parts) ? parts.reduce((acc, p) => acc + (p?.length || 0), 0) : 0
    this.type = options?.type || ''
  }
}
// @ts-expect-error global override for tests
global.Blob = BlobShim as any

class FileShim extends BlobShim {
  name: string
  lastModified: number
  constructor(parts: any[] = [], name = 'file', options: any = {}) {
    super(parts, options)
    this.name = name
    this.lastModified = Date.now()
  }
}
// @ts-expect-error global override for tests
global.File = FileShim as any

class FormDataShim {
  private map = new Map<string, any[]>()
  append(key: string, value: any) { this.set(key, value) }
  delete(key: string) { this.map.delete(key) }
  get(key: string) { const v = this.map.get(key); return v ? v[0] : null }
  getAll(key: string) { return this.map.get(key) || [] }
  has(key: string) { return this.map.has(key) }
  set(key: string, value: any) { this.map.set(key, [value]) }
  forEach(cb: (value: any, key: string) => void) { for (const [k, arr] of this.map) arr.forEach(v => cb(v, k)) }
  *entries() { for (const [k, arr] of this.map) for (const v of arr) yield [k, v] as const }
  *keys() { for (const [k] of this.map) yield k }
  *values() { for (const [, arr] of this.map) for (const v of arr) yield v }
}
// @ts-expect-error global override for tests
global.FormData = FormDataShim as any

// Mock AbortController
global.AbortController = vi.fn().mockImplementation(() => ({
  abort: vi.fn(),
  signal: {
    aborted: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  },
}))

// Mock crypto
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: vi.fn(() => 'mock-uuid'),
    getRandomValues: vi.fn((arr) => arr),
  },
  writable: true,
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
  cleanup()
})

afterAll(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  console.error = originalConsoleError
})
