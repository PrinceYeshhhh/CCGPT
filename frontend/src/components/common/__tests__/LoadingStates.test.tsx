import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { LoadingSpinner, FullPageLoader } from '../../LoadingStates'

describe('LoadingStates', () => {
  it('renders LoadingSpinner', () => {
    render(<LoadingSpinner />)
    const spinner = screen.getByRole('status', { hidden: true })
    expect(spinner).toBeInTheDocument()
  })

  it('renders FullPageLoader', () => {
    render(<FullPageLoader />)
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })
})


