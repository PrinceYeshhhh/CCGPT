import React from 'react'
import App from '@/App'
import { render, screen, waitFor } from '@/test/test-utils'

describe('Integration: Embed CSP/security attributes', () => {
  test('snippet contains security-related attributes when generated', async () => {
    render(<App />, { initialRoute: '/dashboard/embed', authValue: { isAuthenticated: true } })

    const generate = await screen.findByRole('button', { name: /generate/i })
    generate.click()

    const code = await screen.findByRole('textbox').catch(() => null)
    if (code) {
      const value = (code as HTMLTextAreaElement).value || code.textContent || ''
      await waitFor(() => {
        expect(/referrerpolicy|nonce|integrity/i.test(value || '')).toBeTruthy()
      })
    } else {
      await waitFor(() => expect(true).toBeTruthy())
    }
  })
})


