import React from 'react'
import App from '@/App'
import { render, screen } from '@/test/test-utils'

describe('Integration: Documents with MSW', () => {
  test('renders MSW-provided documents', async () => {
    render(<App />, { initialRoute: '/dashboard/documents', authValue: { isAuthenticated: true } })
    const doc1 = await screen.findByText(/Doc 1/i)
    expect(doc1).toBeInTheDocument()
  })
})


