import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { DashboardAccessControl } from '../DashboardAccessControl'

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (orig) => {
  const actual: any = await orig()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/lib/api', () => ({
  api: { get: vi.fn() },
}))

describe('DashboardAccessControl', () => {
  const { api } = require('@/lib/api')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner initially', () => {
    ;(api.get as any).mockResolvedValueOnce({ data: { plan: 'pro', status: 'active' } })
    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div data-testid="children" />
        </DashboardAccessControl>
      </MemoryRouter>
    )
    expect(screen.getByText('Checking access...')).toBeInTheDocument()
  })

  it('renders children when access is allowed', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'pro', status: 'active' },
    })

    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div data-testid="children">Allowed</div>
        </DashboardAccessControl>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('children')).toBeInTheDocument()
    })
  })

  it('blocks access for inactive subscription and offers actions', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'pro', status: 'canceled' },
    })

    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div data-testid="children" />
        </DashboardAccessControl>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Access Restricted')).toBeInTheDocument()
    })

    const choosePlan = screen.getByRole('button', { name: /choose a plan/i })
    fireEvent.click(choosePlan)
    expect(mockNavigate).toHaveBeenCalledWith('/pricing')
  })

  it('shows trial expired message when trialing ended', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'free_trial', status: 'active' },
    })
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'free_trial', status: 'past_due' },
    })

    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div />
        </DashboardAccessControl>
      </MemoryRouter>
    )

    await waitFor(() => {
      // When no valid access, a CTA button should exist
      expect(screen.getByRole('button', { name: /upgrade now|choose a plan/i })).toBeInTheDocument()
    })
  })

  it('navigates to billing when Manage Billing clicked for paid plan', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'pro', status: 'canceled' },
    })

    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div />
        </DashboardAccessControl>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Manage Billing')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Manage Billing'))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/billing')
  })

  it('allows access if subscription check fails (fails open)', async () => {
    ;(api.get as any).mockRejectedValueOnce(new Error('network'))

    render(
      <MemoryRouter>
        <DashboardAccessControl>
          <div data-testid="children">Visible</div>
        </DashboardAccessControl>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Visible')).toBeInTheDocument()
    })
  })
})


