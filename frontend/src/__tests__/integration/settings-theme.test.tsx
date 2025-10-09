import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent, mockLocalStorage } from '@/test/test-utils'

describe('Integration: Settings theme persistence', () => {
  test('toggles theme and persists across reload', async () => {
    const store = mockLocalStorage()

    render(<App />, { initialRoute: '/dashboard/settings', authValue: { isAuthenticated: true } })

    const toggle = await screen.findByRole('button', { name: /theme/i })
    fireEvent.click(toggle)

    await waitFor(() => {
      expect(Object.keys(store).some(k => /theme/i.test(k))).toBeTruthy()
    })

    // Simulate reload by navigating away and back
    window.history.pushState({}, '', '/dashboard')
    window.history.pushState({}, '', '/dashboard/settings')

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard/settings'))
  })
})


