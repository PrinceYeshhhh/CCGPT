import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../accordion'

describe('Accordion', () => {
  it('renders trigger and shows content when defaultValue matches', () => {
    render(
      <Accordion type="single" collapsible defaultValue="item-1">
        <AccordionItem value="item-1">
          <AccordionTrigger>Section 1</AccordionTrigger>
          <AccordionContent>
            <div data-testid="content-1">Content 1</div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    )

    expect(screen.getByText('Section 1')).toBeInTheDocument()
    expect(screen.getByTestId('content-1')).toBeInTheDocument()
  })
})


