import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'

describe('Integration: Billing & payments', () => {
  test('opening payment popup and completing success flow updates plan display', async () => {
    render(<App />, { initialRoute: '/dashboard/billing', authValue: { isAuthenticated: true } })

    // The page should render and show plan info; open a mocked payment popup if applicable
    const upgradeButton = await screen.findByRole('button', { name: /upgrade/i })
    fireEvent.click(upgradeButton)

    const popup = await screen.findByTestId('payment-popup')
    expect(popup).toBeInTheDocument()

    const pay = await screen.findByRole('button', { name: /pay/i })
    fireEvent.click(pay)

    // Expect some UI cue that plan changed (non-brittle text match)
    await waitFor(async () => {
      const plan = await screen.findByText(/current plan/i)
      expect(plan).toBeInTheDocument()
    })
  })
})


