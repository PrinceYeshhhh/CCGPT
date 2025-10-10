import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { LoadingSpinner, LoadingPage } from '../LoadingStates'

describe('LoadingStates', () => {
  it('renders LoadingSpinner', () => {
    render(<LoadingSpinner />)
    // Check that the component renders by looking for the container div
    const container = document.querySelector('.flex.items-center.justify-center.space-x-2')
    expect(container).toBeInTheDocument()
  })

  it('renders LoadingPage', () => {
    render(<LoadingPage />)
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })
})


