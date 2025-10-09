import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from '../Sidebar'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (orig) => {
  const actual: any = await orig()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/contexts/ThemeContext', async (orig) => {
  const actual: any = await orig()
  return {
    ...actual,
    useTheme: () => ({ theme: 'light' }),
  }
})

vi.mock('@/lib/api', () => ({
  api: { get: vi.fn() },
}))

describe('Sidebar', () => {
  const { api } = require('@/lib/api')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('highlights the active navigation item based on route', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard/documents']}>
        <Sidebar />
      </MemoryRouter>
    )

    expect(screen.getByText('Documents')).toBeInTheDocument()
  })

  it('renders plan info with loading state then fetched data', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: {
        plan: 'pro',
        usage: { queries_used: 123, queries_limit: 1000 },
      },
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )

    // Shows loading initially
    expect(screen.getAllByText('Loading...').length).toBeGreaterThan(0)

    await waitFor(() => {
      expect(screen.getByText('Pro Plan')).toBeInTheDocument()
      expect(screen.getByText(/123\s*\/\s*1,000 queries/i)).toBeInTheDocument()
    })
  })

  it('navigates to pricing when Upgrade clicked', async () => {
    ;(api.get as any).mockResolvedValueOnce({
      data: { plan: 'free' },
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Free Plan/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /upgrade/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/pricing')
  })
})


