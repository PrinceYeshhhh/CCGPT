import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { DashboardLayout } from '../../DashboardLayout'

describe('DashboardLayout', () => {
  it('renders layout and outlet area', () => {
    render(
      <MemoryRouter>
        <DashboardLayout />
      </MemoryRouter>
    )
    // Basic structure checks depending on implementation
    expect(screen.getByTestId('dashboard-layout')).toBeInTheDocument()
  })
})


