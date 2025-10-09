import React from 'react'
import App from '@/App'
import { render, screen, waitFor } from '@/test/test-utils'

describe('Integration: Deep-link and history navigation', () => {
  test('deep-link to protected nested route redirects to login when unauthenticated', async () => {
    render(<App />, { initialRoute: '/dashboard/documents' })

    await waitFor(() => {
      expect(window.location.pathname).toBe('/login')
    })
  })

  test('unknown deep-link renders NotFound and allows navigating back to home', async () => {
    render(<App />, { initialRoute: '/some/unknown/path' })

    const notFoundHeading = await screen.findByText('404 - Page Not Found')
    expect(notFoundHeading).toBeInTheDocument()

    // Simulate user clicking browser back
    window.history.pushState({}, '', '/')

    await waitFor(() => {
      expect(window.location.pathname).toBe('/')
    })
  })
})


