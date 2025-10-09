// Test data factories for consistent test data generation

export interface MockUser {
  id: string
  email: string
  name: string
  plan: 'free' | 'pro' | 'enterprise'
  isActive: boolean
  createdAt: string
  updatedAt: string
  subscriptionId?: string
  trialEndsAt?: string
  usage?: {
    documents: number
    queries: number
    storage: number
  }
}

export interface MockDocument {
  id: string
  name: string
  type: string
  size: number
  status: 'processing' | 'ready' | 'error'
  createdAt: string
  updatedAt: string
  content?: string
  metadata?: Record<string, any>
}

export interface MockChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messages: MockMessage[]
  documentIds: string[]
}

export interface MockMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface MockAnalytics {
  totalQueries: number
  totalDocuments: number
  totalSessions: number
  averageResponseTime: number
  queriesByDay: Array<{ date: string; count: number }>
  documentsByType: Array<{ type: string; count: number }>
  topQueries: Array<{ query: string; count: number }>
}

export interface MockBilling {
  currentPlan: 'free' | 'pro' | 'enterprise'
  status: 'active' | 'canceled' | 'past_due'
  currentPeriodStart: string
  currentPeriodEnd: string
  cancelAtPeriodEnd: boolean
  usage: {
    documents: number
    queries: number
    storage: number
  }
  limits: {
    documents: number
    queries: number
    storage: number
  }
  nextInvoice?: {
    amount: number
    currency: string
    date: string
  }
}

export interface MockWidget {
  id: string
  name: string
  domain: string
  isActive: boolean
  createdAt: string
  updatedAt: string
  settings: {
    theme: 'light' | 'dark' | 'auto'
    position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
    size: 'small' | 'medium' | 'large'
    showBranding: boolean
    customCss?: string
  }
  stats: {
    totalViews: number
    totalInteractions: number
    averageSessionDuration: number
  }
}

// User factories
export const createMockUser = (overrides: Partial<MockUser> = {}): MockUser => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  plan: 'pro',
  isActive: true,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  subscriptionId: 'sub_123',
  trialEndsAt: '2023-02-01T00:00:00Z',
  usage: {
    documents: 5,
    queries: 100,
    storage: 1024 * 1024 * 10, // 10MB
  },
  ...overrides,
})

export const createMockFreeUser = (overrides: Partial<MockUser> = {}): MockUser =>
  createMockUser({
    plan: 'free',
    subscriptionId: undefined,
    trialEndsAt: undefined,
    usage: {
      documents: 2,
      queries: 50,
      storage: 1024 * 1024 * 5, // 5MB
    },
    ...overrides,
  })

export const createMockProUser = (overrides: Partial<MockUser> = {}): MockUser =>
  createMockUser({
    plan: 'pro',
    subscriptionId: 'sub_pro_123',
    usage: {
      documents: 50,
      queries: 1000,
      storage: 1024 * 1024 * 100, // 100MB
    },
    ...overrides,
  })

export const createMockEnterpriseUser = (overrides: Partial<MockUser> = {}): MockUser =>
  createMockUser({
    plan: 'enterprise',
    subscriptionId: 'sub_enterprise_123',
    usage: {
      documents: 500,
      queries: 10000,
      storage: 1024 * 1024 * 1000, // 1GB
    },
    ...overrides,
  })

// Document factories
export const createMockDocument = (overrides: Partial<MockDocument> = {}): MockDocument => ({
  id: 'doc-123',
  name: 'test-document.pdf',
  type: 'application/pdf',
  size: 1024 * 1024, // 1MB
  status: 'ready',
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  content: 'This is test document content',
  metadata: {
    pages: 10,
    language: 'en',
    author: 'Test Author',
  },
  ...overrides,
})

export const createMockProcessingDocument = (overrides: Partial<MockDocument> = {}): MockDocument =>
  createMockDocument({
    status: 'processing',
    content: undefined,
    metadata: undefined,
    ...overrides,
  })

export const createMockErrorDocument = (overrides: Partial<MockDocument> = {}): MockDocument =>
  createMockDocument({
    status: 'error',
    content: undefined,
    metadata: { error: 'Failed to process document' },
    ...overrides,
  })

// Chat session factories
export const createMockChatSession = (overrides: Partial<MockChatSession> = {}): MockChatSession => ({
  id: 'session-123',
  title: 'Test Chat Session',
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  messages: [
    createMockMessage({ role: 'user', content: 'Hello, how can you help me?' }),
    createMockMessage({ role: 'assistant', content: 'I can help you with questions about your documents.' }),
  ],
  documentIds: ['doc-123'],
  ...overrides,
})

export const createMockMessage = (overrides: Partial<MockMessage> = {}): MockMessage => ({
  id: 'msg-123',
  role: 'user',
  content: 'Test message',
  timestamp: '2023-01-01T00:00:00Z',
  metadata: {},
  ...overrides,
})

// Analytics factories
export const createMockAnalytics = (overrides: Partial<MockAnalytics> = {}): MockAnalytics => ({
  totalQueries: 1000,
  totalDocuments: 50,
  totalSessions: 100,
  averageResponseTime: 1.5,
  queriesByDay: [
    { date: '2023-01-01', count: 50 },
    { date: '2023-01-02', count: 75 },
    { date: '2023-01-03', count: 100 },
  ],
  documentsByType: [
    { type: 'application/pdf', count: 30 },
    { type: 'text/plain', count: 20 },
  ],
  topQueries: [
    { query: 'How do I reset my password?', count: 25 },
    { query: 'What is the refund policy?', count: 20 },
  ],
  ...overrides,
})

// Billing factories
export const createMockBilling = (overrides: Partial<MockBilling> = {}): MockBilling => ({
  currentPlan: 'pro',
  status: 'active',
  currentPeriodStart: '2023-01-01T00:00:00Z',
  currentPeriodEnd: '2023-02-01T00:00:00Z',
  cancelAtPeriodEnd: false,
  usage: {
    documents: 25,
    queries: 500,
    storage: 1024 * 1024 * 50, // 50MB
  },
  limits: {
    documents: 100,
    queries: 1000,
    storage: 1024 * 1024 * 100, // 100MB
  },
  nextInvoice: {
    amount: 2900, // $29.00 in cents
    currency: 'usd',
    date: '2023-02-01T00:00:00Z',
  },
  ...overrides,
})

export const createMockFreeBilling = (overrides: Partial<MockBilling> = {}): MockBilling =>
  createMockBilling({
    currentPlan: 'free',
    status: 'active',
    usage: {
      documents: 2,
      queries: 50,
      storage: 1024 * 1024 * 5, // 5MB
    },
    limits: {
      documents: 5,
      queries: 100,
      storage: 1024 * 1024 * 10, // 10MB
    },
    nextInvoice: undefined,
    ...overrides,
  })

// Widget factories
export const createMockWidget = (overrides: Partial<MockWidget> = {}): MockWidget => ({
  id: 'widget-123',
  name: 'Test Widget',
  domain: 'example.com',
  isActive: true,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  settings: {
    theme: 'light',
    position: 'bottom-right',
    size: 'medium',
    showBranding: true,
  },
  stats: {
    totalViews: 1000,
    totalInteractions: 500,
    averageSessionDuration: 120, // 2 minutes
  },
  ...overrides,
})

// API response factories
export const createMockApiResponse = <T>(data: T, status: number = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
})

export const createMockApiError = (message: string = 'Internal Server Error', status: number = 500) => ({
  ok: false,
  status,
  json: () => Promise.resolve({ error: message }),
  text: () => Promise.resolve(JSON.stringify({ error: message })),
})

// Common test data sets
export const mockUsers = {
  free: createMockFreeUser(),
  pro: createMockProUser(),
  enterprise: createMockEnterpriseUser(),
}

export const mockDocuments = {
  ready: createMockDocument(),
  processing: createMockProcessingDocument(),
  error: createMockErrorDocument(),
}

export const mockBilling = {
  free: createMockFreeBilling(),
  pro: createMockBilling(),
}

export const mockWidgets = {
  active: createMockWidget(),
  inactive: createMockWidget({ isActive: false }),
}

// Utility functions for test data
export const generateMockId = (prefix: string = 'test') => `${prefix}-${Math.random().toString(36).substr(2, 9)}`

export const generateMockEmail = (domain: string = 'example.com') => `test-${Math.random().toString(36).substr(2, 9)}@${domain}`

export const generateMockDate = (daysAgo: number = 0) => {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString()
}

export const generateMockArray = <T>(factory: () => T, count: number): T[] => {
  return Array.from({ length: count }, factory)
}

// Mock file for testing file uploads
export const createMockFile = (name: string, type: string, size: number = 1024) => {
  const file = new File(['test content'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
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

// Mock URL search params
export const createMockSearchParams = (params: Record<string, string>) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    searchParams.set(key, value)
  })
  return searchParams
}

// Mock location object
export const createMockLocation = (pathname: string = '/', search: string = '', hash: string = '') => ({
  pathname,
  search,
  hash,
  href: `http://localhost:3000${pathname}${search}${hash}`,
  origin: 'http://localhost:3000',
  protocol: 'http:',
  host: 'localhost:3000',
  hostname: 'localhost',
  port: '3000',
  assign: vi.fn(),
  replace: vi.fn(),
  reload: vi.fn(),
})

// Mock history object
export const createMockHistory = () => ({
  pushState: vi.fn(),
  replaceState: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  length: 1,
  state: null,
})

// Mock window object
export const createMockWindow = (overrides: Partial<Window> = {}) => ({
  location: createMockLocation(),
  history: createMockHistory(),
  localStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  sessionStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  fetch: vi.fn(),
  alert: vi.fn(),
  confirm: vi.fn(() => true),
  prompt: vi.fn(() => ''),
  scrollTo: vi.fn(),
  ...overrides,
})

// Import vi for the mocks
import { vi } from 'vitest'
