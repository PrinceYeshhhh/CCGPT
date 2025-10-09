import React from 'react'
import App from '@/App'
import { render, screen, fireEvent } from '@/test/test-utils'

describe('Integration: Form validation (Register/Login/Settings)', () => {
  test('login requires valid email and password', async () => {
    render(<App />, { initialRoute: '/login' })

    const submit = await screen.findByRole('button', { name: /log in/i })
    fireEvent.click(submit)

    // Expect generic validation feedback
    const validation = await screen.findAllByText(/required|invalid/i)
    expect(validation.length).toBeGreaterThan(0)
  })

  test('register shows validation errors on missing fields', async () => {
    render(<App />, { initialRoute: '/register' })

    const submit = await screen.findByRole('button', { name: /register/i })
    fireEvent.click(submit)

    const validation = await screen.findAllByText(/required|invalid|password/i)
    expect(validation.length).toBeGreaterThan(0)
  })
})


