import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import WidgetBehaviorControl from '../../WidgetBehaviorControl'

describe('WidgetBehaviorControl', () => {
  it('renders and toggles options', () => {
    const onChange = vi.fn()
    render(<WidgetBehaviorControl value={{ draggable: true, minimized: false }} onChange={onChange} />)

    const draggable = screen.getByLabelText(/draggable/i)
    fireEvent.click(draggable)
    expect(onChange).toHaveBeenCalled()
  })
})


