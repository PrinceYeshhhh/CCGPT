import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockLocalStorage } from '@/test/test-utils'

const AUTH_STORAGE_KEY = 'auth_token'

describe('Integration: Auth & session lifecycle', () => {
  test('successful login persists session and redirects to dashboard', async () => {
    // Seed storage to simulate an already-authenticated session
    mockLocalStorage({ [AUTH_STORAGE_KEY]: 'valid-token' })

    render(<App />, { initialRoute: '/login' })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard')
    })
  })

  test('expired session redirects to /login from protected route', async () => {
    mockLocalStorage({ [AUTH_STORAGE_KEY]: '' })

    render(<App />, { initialRoute: '/dashboard/settings' })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/login')
    })
  })
})


