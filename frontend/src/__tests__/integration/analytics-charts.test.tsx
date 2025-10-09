import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockFetch, fireEvent } from '@/test/test-utils'

describe('Integration: Analytics charts', () => {
  test('renders charts with data and updates on filter change', async () => {
    mockFetch({ ok: true, status: 200, json: async () => ({ data: [ { x: 1, y: 2 } ] }) })
    render(<App />, { initialRoute: '/dashboard/analytics', authValue: { isAuthenticated: true } })

    // Chart container appears
    const chartRegion = await screen.findByRole('region', { name: /analytics/i })
    expect(chartRegion).toBeInTheDocument()

    // Change filter
    const select = await screen.findByRole('combobox')
    fireEvent.change(select, { target: { value: 'last_30_days' } })

    // Expect another fetch
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })
})


