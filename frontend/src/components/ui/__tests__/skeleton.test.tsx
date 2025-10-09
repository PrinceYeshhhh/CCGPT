import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Skeleton } from '../skeleton'

describe('Skeleton', () => {
  it('renders with default class', () => {
    render(<Skeleton data-testid="sk" />)
    const el = screen.getByTestId('sk')
    expect(el).toBeInTheDocument()
    expect(el).toHaveClass('animate-pulse')
  })

  it('accepts custom className', () => {
    render(<Skeleton className="h-6 w-24" data-testid="sk2" />)
    const el = screen.getByTestId('sk2')
    expect(el).toHaveClass('h-6', 'w-24')
  })
})


