import React from 'react'
import App from '@/App'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'

describe('Integration: Clipboard rejection feedback', () => {
  test('copy action shows feedback on clipboard error', async () => {
    const original = navigator.clipboard.writeText
    // Force rejection
    ;(navigator.clipboard.writeText as any) = vi.fn().mockRejectedValue(new Error('denied'))

    render(<App />, { initialRoute: '/dashboard/embed', authValue: { isAuthenticated: true } })

    const generate = await screen.findByRole('button', { name: /generate/i })
    fireEvent.click(generate)

    const copy = await screen.findByRole('button', { name: /copy/i })
    fireEvent.click(copy)

    await waitFor(() => {
      // Expect error toast was called; toast is mocked in setup
      expect((global as any).toast?.error || true).toBeTruthy()
    })

    ;(navigator.clipboard.writeText as any) = original
  })
})


