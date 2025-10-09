import React from 'react'
import App from '@/App'
import { render, waitFor } from '@/test/test-utils'

describe('Integration: Demo mode nested routes', () => {
  test('allows direct access to nested dashboard route when demo mode enabled', async () => {
    ;(import.meta as any).env = { ...(import.meta as any).env, VITE_DEMO_MODE: 'true' }
    render(<App />, { initialRoute: '/dashboard/analytics' })

    await waitFor(() => expect(window.location.pathname).toBe('/dashboard/analytics'))
  })
})


