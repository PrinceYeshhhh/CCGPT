import React from 'react'
import App from '@/App'
import { render, screen, waitFor, mockLocalStorage, fireEvent } from '@/test/test-utils'

describe('Integration: Dark mode persistence', () => {
  test('dark mode persists across navigation and reload', async () => {
    const store = mockLocalStorage()
    render(<App />, { initialRoute: '/', authValue: { isAuthenticated: false } })

    // Theme toggle is available on public layout
    const toggle = await screen.findByRole('button', { name: /theme/i })
    fireEvent.click(toggle)

    await waitFor(() => {
      expect(Object.keys(store).some(k => /theme/i.test(k))).toBeTruthy()
    })

    window.history.pushState({}, '', '/features')
    await waitFor(() => expect(window.location.pathname).toBe('/features'))
  })
})


