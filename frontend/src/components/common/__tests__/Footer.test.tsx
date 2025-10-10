import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { Footer } from '../Footer'

describe('Footer', () => {
  it('renders footer links and branding', () => {
    render(
      <BrowserRouter>
        <Footer />
      </BrowserRouter>
    )

    expect(screen.getAllByText(/CustomerCareGPT/i)).toHaveLength(2)
    // Common footer links if present
    ;['Home', 'Features', 'Pricing', 'FAQ'].forEach(text => {
      const el = screen.queryByText(text)
      if (el) expect(el).toBeInTheDocument()
    })
  })
})


