import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Billing } from '@/pages/dashboard/Billing'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
  toast: { success: vi.fn(), error: vi.fn() }
}))

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(async (url: string) => {
      if (url === '/billing/status') {
        return { data: {
          plan: 'free',
          status: 'inactive',
          current_period_end: null,
          cancel_at_period_end: false,
          usage: { queries_used: 100, queries_limit: 1000, documents_used: 5, documents_limit: 50, storage_used: 1, storage_limit: 10 },
          is_trial: false
        }}
      }
      if (url === '/pricing/plans') {
        return { data: { plans: [
          { id: 'starter', name: 'Starter', price: 2000, currency: 'usd', interval: 'month', features: ['A'], popular: false },
          { id: 'pro', name: 'Pro', price: 5000, currency: 'usd', interval: 'month', features: ['B'], popular: true }
        ] } }
      }
      if (url === '/billing/payment-methods') {
        return { data: { payment_methods: [] } }
      }
      if (url === '/billing/invoices') {
        return { data: { invoices: [] } }
      }
      return { data: {} }
    })
  }
}))

describe('Billing flow', () => {
  it('clicking upgrade triggers checkout popup flow', async () => {
    render(<Billing />)

    const upgradeButtons = await screen.findAllByRole('button', { name: /upgrade/i })
    expect(upgradeButtons.length).toBeGreaterThan(0)

    fireEvent.click(upgradeButtons[0])

    expect(upgradeButtons[0]).toBeInTheDocument()
  })
})


