import React from 'react'
import App from '@/App'
import { render, waitFor, mockFetch } from '@/test/test-utils'

describe('Integration: Documents route', () => {
  test('navigating to documents triggers data fetch when authenticated', async () => {
    // Mock a successful fetch response (shape not asserted here to avoid tight coupling)
    mockFetch({ ok: true, status: 200, json: async () => ({}) })

    render(<App />, {
      initialRoute: '/dashboard/documents',
      authValue: { isAuthenticated: true },
    })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard/documents')
    })

    // Ensure the page attempted to fetch data at least once
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })
})


