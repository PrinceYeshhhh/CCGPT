import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ThemeToggle } from '../theme-toggle'

const mockToggleTheme = vi.fn()

vi.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({ 
    theme: 'light', 
    toggleTheme: mockToggleTheme 
  }),
}))

describe('ThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders button with correct aria-label and triggers toggle', () => {
    render(<ThemeToggle />)
    const btn = screen.getByRole('button', { name: /switch to dark theme/i })
    fireEvent.click(btn)
    expect(mockToggleTheme).toHaveBeenCalled()
  })
})


