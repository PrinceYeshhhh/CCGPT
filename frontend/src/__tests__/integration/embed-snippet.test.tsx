import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'

describe('Integration: Embed snippet', () => {
  test('generates snippet and copies to clipboard', async () => {
    render(<App />, { initialRoute: '/dashboard/embed', authValue: { isAuthenticated: true } })

    const generate = await screen.findByRole('button', { name: /generate/i })
    fireEvent.click(generate)

    const preview = await screen.findByTestId(/widget-preview/i)
    expect(preview).toBeInTheDocument()

    const copy = await screen.findByRole('button', { name: /copy/i })
    fireEvent.click(copy)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toBeCalled()
    })
  })
})


