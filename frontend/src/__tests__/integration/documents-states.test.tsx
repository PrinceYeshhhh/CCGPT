import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockFetch } from '@/test/test-utils'

describe('Integration: Documents states', () => {
  test('renders empty state when no documents', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ items: [] }) })
    render(<App />, { initialRoute: '/dashboard/documents', authValue: { isAuthenticated: true } })

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard/documents'))

    // Generic empty state cue: text or role from page implementation (non-brittle)
    const empty = await screen.findByText(/no documents/i)
    expect(empty).toBeInTheDocument()
  })

  test('renders error state on API failure', async () => {
    mockFetch({ ok: false, status: 500, json: async () => ({ error: 'boom' }) })
    render(<App />, { initialRoute: '/dashboard/documents', authValue: { isAuthenticated: true } })

    const error = await screen.findByText(/error/i)
    expect(error).toBeInTheDocument()
  })
})


