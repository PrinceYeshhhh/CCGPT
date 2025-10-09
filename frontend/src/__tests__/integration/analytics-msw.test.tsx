import React from 'react'
import App from '@/App'
import { render, screen } from '@/test/test-utils'

describe('Integration: Analytics with MSW', () => {
  test('renders chart region based on MSW data', async () => {
    render(<App />, { initialRoute: '/dashboard/analytics', authValue: { isAuthenticated: true } })
    const region = await screen.findByRole('region', { name: /analytics/i })
    expect(region).toBeInTheDocument()
  })
})


