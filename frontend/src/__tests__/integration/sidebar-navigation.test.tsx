import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'

describe('Integration: Dashboard Sidebar navigation', () => {
  test('navigates across primary routes and highlights active link', async () => {
    render(<App />, { initialRoute: '/dashboard', authValue: { isAuthenticated: true } })

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard'))

    // Click on Documents
    const documentsLink = await screen.findByRole('link', { name: /documents/i })
    fireEvent.click(documentsLink)

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard/documents'))

    // Click on Analytics
    const analyticsLink = await screen.findByRole('link', { name: /analytics/i })
    fireEvent.click(analyticsLink)

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard/analytics'))
  })
})


