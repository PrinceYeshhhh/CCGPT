import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Textarea } from '../textarea'

describe('Textarea', () => {
  it('renders and accepts typing', () => {
    render(<Textarea placeholder="Enter text" />)
    const el = screen.getByPlaceholderText('Enter text') as HTMLTextAreaElement
    fireEvent.change(el, { target: { value: 'hello world' } })
    expect(el.value).toBe('hello world')
  })
})


