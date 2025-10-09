import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'

describe('Integration: Settings API keys', () => {
  test('regenerates API key and copies to clipboard', async () => {
    render(<App />, { initialRoute: '/dashboard/settings', authValue: { isAuthenticated: true } })

    const regenerate = await screen.findByRole('button', { name: /regenerate api key/i })
    fireEvent.click(regenerate)

    const copy = await screen.findByRole('button', { name: /copy api key/i })
    fireEvent.click(copy)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toBeCalled()
    })
  })
})


