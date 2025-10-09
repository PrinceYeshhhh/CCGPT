import React from 'react'
import App from '@/App'
import { render } from '@/test/test-utils'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Integration: Accessibility (axe)', () => {
  test('Home has no critical accessibility violations', async () => {
    const { container } = render(<App />, { initialRoute: '/' })
    const results = await axe(container, { rules: { region: { enabled: true } } })
    expect(results).toHaveNoViolations()
  })

  test('Billing dialog has no critical violations when open', async () => {
    const { container, findByRole, getByRole } = render(<App />, { initialRoute: '/dashboard/billing', authValue: { isAuthenticated: true } })
    const open = await findByRole('button', { name: /upgrade/i })
    open.click()
    await findByRole('dialog')
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})


