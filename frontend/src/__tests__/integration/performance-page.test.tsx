import React from 'react'
import App from '@/App'
import { render, screen } from '@/test/test-utils'

describe('Integration: Performance page', () => {
  test('renders with mocked performance APIs present', async () => {
    render(<App />, { initialRoute: '/dashboard/performance', authValue: { isAuthenticated: true } })

    const heading = await screen.findByText(/performance/i)
    expect(heading).toBeInTheDocument()
  })
})


