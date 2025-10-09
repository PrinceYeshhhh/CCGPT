import React from 'react'
import App from '@/App'
import { render, screen } from '@/test/test-utils'

describe('Integration: Billing with MSW', () => {
  test('shows current plan from MSW handler', async () => {
    render(<App />, { initialRoute: '/dashboard/billing', authValue: { isAuthenticated: true } })
    const plan = await screen.findByText(/current plan/i)
    expect(plan).toBeInTheDocument()
  })
})


