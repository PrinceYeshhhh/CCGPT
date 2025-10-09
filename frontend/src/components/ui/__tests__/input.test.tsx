import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Input } from '../input'

describe('Input', () => {
  it('renders and accepts typing', () => {
    render(<Input placeholder="Type here" />)
    const el = screen.getByPlaceholderText('Type here') as HTMLInputElement
    fireEvent.change(el, { target: { value: 'hello' } })
    expect(el.value).toBe('hello')
  })
})


