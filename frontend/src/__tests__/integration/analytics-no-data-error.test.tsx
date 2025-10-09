import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockFetch } from '@/test/test-utils'

describe('Integration: Analytics no-data and error placeholders', () => {
  test('renders no-data placeholder when dataset empty', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ data: [] }) })
    render(<App />, { initialRoute: '/dashboard/analytics', authValue: { isAuthenticated: true } })

    const placeholder = await screen.findByText(/no data/i)
    expect(placeholder).toBeInTheDocument()
  })

  test('renders error placeholder on API failure', async () => {
    mockFetch({ ok: false, status: 500, json: async () => ({ error: 'boom' }) })
    render(<App />, { initialRoute: '/dashboard/analytics', authValue: { isAuthenticated: true } })

    const error = await screen.findByText(/error/i)
    expect(error).toBeInTheDocument()
  })
})


