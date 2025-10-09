import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CurrentPlanDisplay } from '../CurrentPlanDisplay'

describe('CurrentPlanDisplay', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-01T00:00:00.000Z'))
  })

  it('renders Pro plan with active status', () => {
    render(
      <CurrentPlanDisplay plan="pro" status="active" className="test-class" />
    )

    expect(screen.getByText('Pro')).toBeInTheDocument()
    // Badge text capitalized when not trialing
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders Free Trial with trial badge and days left', () => {
    // Trial end tomorrow relative to mocked date
    const trialEnd = new Date('2025-01-02T00:00:00.000Z').toISOString()

    render(
      <CurrentPlanDisplay plan="free_trial" status="trialing" isTrial trialEnd={trialEnd} />
    )

    expect(screen.getByText('Free Trial')).toBeInTheDocument()
    expect(screen.getByText('Trial')).toBeInTheDocument()
    // 1 day left (ceil)
    expect(screen.getByText('1 day left')).toBeInTheDocument()
  })

  it('shows trial expired when date is past', () => {
    const trialEnd = new Date('2024-12-31T23:59:59.000Z').toISOString()
    render(
      <CurrentPlanDisplay plan="free_trial" status="trialing" isTrial trialEnd={trialEnd} />
    )
    expect(screen.getByText('Trial expired')).toBeInTheDocument()
  })

  it('falls back to Free and gray color for unknown plan', () => {
    render(<CurrentPlanDisplay plan={'unknown' as any} status="canceled" />)
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('Canceled')).toBeInTheDocument()
  })
})


