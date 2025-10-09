import React from 'react'
import App from '@/App'
import { render, screen } from '@/test/test-utils'

// Minimal smoke to ensure key routes mount stable DOM structure and titles
describe('Integration: Visual smoke across core routes', () => {
  const routes = ['/', '/features', '/pricing', '/faq']

  test.each(routes)('renders route %s without crashing', async (route) => {
    render(<App />, { initialRoute: route })

    // Navbar should exist on all public routes
    const nav = await screen.findByRole('navigation')
    expect(nav).toBeInTheDocument()
  })
})


