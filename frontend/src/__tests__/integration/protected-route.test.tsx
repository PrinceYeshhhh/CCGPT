import React from 'react'
import { beforeEach } from 'vitest'
import { render, waitFor } from '@/test/test-utils'

// Import App dynamically within tests if we need to adjust env in future
import App from '@/App'

describe('Integration: ProtectedRoute', () => {
  beforeEach(() => {
    // Ensure demo mode is off by default
    ;(import.meta as any).env = { ...(import.meta as any).env, VITE_DEMO_MODE: 'false' }
  })

  test('redirects unauthenticated user to /login when demo mode is disabled', async () => {
    render(<App />, { initialRoute: '/dashboard' })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/login')
    })
  })

  test('allows access to protected routes when demo mode is enabled', async () => {
    ;(import.meta as any).env = { ...(import.meta as any).env, VITE_DEMO_MODE: 'true' }

    render(<App />, { initialRoute: '/dashboard' })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard')
    })
  })
})


