import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../tabs'

describe('Tabs', () => {
  it('renders active tab content with defaultValue', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">
          <div data-testid="content-1">Content 1</div>
        </TabsContent>
        <TabsContent value="tab2">
          <div data-testid="content-2">Content 2</div>
        </TabsContent>
      </Tabs>
    )

    expect(screen.getByTestId('content-1')).toBeInTheDocument()
  })
})


