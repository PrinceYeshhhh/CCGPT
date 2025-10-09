import React from 'react'
import App from '@/App'
import { render, screen, waitFor } from '@/test/test-utils'

describe('Integration: App routing', () => {
  test('unauthenticated user is redirected from protected route to /login', async () => {
    render(<App />, { initialRoute: '/dashboard' })

    await waitFor(() => {
      // Expect login screen to be visible via a common cue
      // We assert by URL change rather than specific login content to avoid coupling
      expect(window.location.pathname).toBe('/login')
    })
  })

  test('unknown route renders NotFound page', async () => {
    render(<App />, { initialRoute: '/this-route-does-not-exist' })

    const notFoundHeading = await screen.findByText('404 - Page Not Found')
    expect(notFoundHeading).toBeInTheDocument()
  })
})


