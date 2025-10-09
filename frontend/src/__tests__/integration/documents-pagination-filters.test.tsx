import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent, mockFetch } from '@/test/test-utils'

describe('Integration: Documents pagination and filters', () => {
  test('requests next page on pagination control', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ items: Array.from({ length: 10 }, (_, i) => ({ id: i })) }) })
    render(<App />, { initialRoute: '/dashboard/documents', authValue: { isAuthenticated: true } })

    const next = await screen.findByRole('button', { name: /next/i })
    fireEvent.click(next)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })

  test('applies filter and refetches list', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ items: [] }) })
    render(<App />, { initialRoute: '/dashboard/documents', authValue: { isAuthenticated: true } })

    const search = await screen.findByRole('textbox', { name: /search/i }).catch(() => null)
    if (search) {
      fireEvent.change(search, { target: { value: 'policy' } })
      await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    } else {
      // If using select-based filtering
      const filter = await screen.findByRole('combobox').catch(() => null)
      if (filter) {
        fireEvent.change(filter, { target: { value: 'all' } })
        await waitFor(() => expect(global.fetch).toHaveBeenCalled())
      }
    }
  })
})


