import React from 'react'
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext'

const TestThemeToggle = () => {
  const { theme, toggleTheme } = useTheme()
  return (
    <button onClick={toggleTheme} aria-label="toggle-theme">{theme}</button>
  )
}

describe('Dark mode persistence', () => {
  beforeEach(() => {
    // reset root classes and storage
    document.documentElement.className = ''
    window.localStorage.clear()
  })

  it('toggles theme and persists to localStorage', async () => {
    render(
      <ThemeProvider>
        <TestThemeToggle />
      </ThemeProvider>
    )

    const btn = screen.getByRole('button', { name: 'toggle-theme' })
    // initial render chooses based on matchMedia; we only verify toggle persists
    fireEvent.click(btn)
    // wait for effect to run and localStorage to update
    // localStorage in setup is mocked; assert that setItem was called and root class toggled
    expect(window.localStorage.setItem).toHaveBeenCalledWith('theme', expect.any(String))
    expect(
      document.documentElement.classList.contains('dark') ||
      document.documentElement.classList.contains('light')
    ).toBe(true)

    const firstTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
    fireEvent.click(btn)
    const now = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
    expect(now).not.toBe(firstTheme)
  })

  it('applies/removes dark class on root element', () => {
    render(
      <ThemeProvider>
        <TestThemeToggle />
      </ThemeProvider>
    )

    const btn = screen.getByRole('button', { name: 'toggle-theme' })
    fireEvent.click(btn)
    expect(
      document.documentElement.classList.contains('dark') ||
      document.documentElement.classList.contains('light')
    ).toBe(true)

    const prev = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
    fireEvent.click(btn)
    const now = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
    expect(now).not.toBe(prev)
  })
})


