import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { OptimizedImage } from '../optimized-image'

describe('OptimizedImage', () => {
  it('renders with required props', () => {
    render(<OptimizedImage src="https://example.com/a.png" alt="Example" width={200} height={100} />)
    const img = screen.getByAltText('Example') as HTMLImageElement
    expect(img).toBeInTheDocument()
    expect(img.src).toContain('https://example.com/a.png')
  })

  it('applies className and style', () => {
    render(
      <OptimizedImage
        src="/image.jpg"
        alt="Styled"
        width={100}
        height={50}
        className="rounded"
        style={{ objectFit: 'cover' }}
      />
    )
    const img = screen.getByAltText('Styled')
    expect(img).toHaveClass('rounded')
  })

  it('supports lazy loading', () => {
    render(<OptimizedImage src="/lazy.jpg" alt="Lazy" width={10} height={5} loading="lazy" />)
    const img = screen.getByAltText('Lazy')
    expect(img).toHaveAttribute('loading', 'lazy')
  })
})


