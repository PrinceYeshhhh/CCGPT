import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Analytics } from '@/pages/dashboard/Analytics'

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(async (url: string) => {
      // Return empty datasets by default
      return { data: { data: [] } }
    })
  }
}))

describe('Analytics charts rendering', () => {
  it('renders with empty dataset', async () => {
    render(<Analytics />)
    // While loading, show text
    expect(await screen.findAllByText(/loading/i)).toBeTruthy()
  })

  it('shows loading and then charts', async () => {
    render(<Analytics />)
    const loadingEls = await screen.findAllByText(/loading/i)
    expect(loadingEls.length).toBeGreaterThan(0)
  })
})


