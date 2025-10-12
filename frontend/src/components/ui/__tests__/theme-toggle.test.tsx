import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ThemeToggle } from '../theme-toggle'

vi.mock('@/contexts/ThemeContext', async (orig) => {
  const actual: any = await orig()
  return {
    ...actual,
    useTheme: () => ({ theme: 'light', toggleTheme: vi.fn() }),
  }
})

describe('ThemeToggle', () => {
  it('renders button with correct aria-label and triggers toggle', () => {
    const { useTheme } = require('@/contexts/ThemeContext')
    const spy = vi.fn()
    useTheme.mockReturnValue({ theme: 'light', toggleTheme: spy })

    act(() => {
      render(<ThemeToggle />)
    })
    const btn = screen.getByRole('button', { name: /switch to dark theme/i })
    fireEvent.click(btn)
    expect(spy).toHaveBeenCalled()
  })
})


