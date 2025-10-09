import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockFetch } from '@/test/test-utils'

describe('Integration: React Query retry/backoff behavior', () => {
  test('shows final error after retries exhausted', async () => {
    let call = 0
    ;(global.fetch as any) = vi.fn(async () => {
      call++
      return { ok: false, status: 500, json: async () => ({ error: 'boom '+call }) }
    })

    render(<App />, { initialRoute: '/dashboard/analytics', authValue: { isAuthenticated: true } })

    const err = await screen.findByText(/error/i)
    expect(err).toBeInTheDocument()
  })
})


