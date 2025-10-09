import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../select'

describe('Select', () => {
  it('renders trigger and options content', () => {
    render(
      <Select defaultOpen>
        <SelectTrigger>
          <SelectValue placeholder="Pick one" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="one">One</SelectItem>
          <SelectItem value="two">Two</SelectItem>
        </SelectContent>
      </Select>
    )

    expect(screen.getByText('Pick one')).toBeInTheDocument()
    expect(screen.getByText('One')).toBeInTheDocument()
    expect(screen.getByText('Two')).toBeInTheDocument()
  })
})


