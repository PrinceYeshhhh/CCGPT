import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../card';

describe('Card', () => {
  it('should render Card with default props', () => {
    render(<Card>Card content</Card>);
    
    const card = screen.getByText('Card content').closest('div');
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('rounded-lg', 'border', 'bg-card', 'text-card-foreground', 'shadow-sm');
  });

  it('should render CardHeader with title and description', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
      </Card>
    );
    
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card Description')).toBeInTheDocument();
    
    const header = screen.getByText('Card Title').closest('div');
    expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6');
  });

  it('should render CardContent', () => {
    render(
      <Card>
        <CardContent>
          <p>Card content text</p>
        </CardContent>
      </Card>
    );
    
    expect(screen.getByText('Card content text')).toBeInTheDocument();
    
    const content = screen.getByText('Card content text').closest('div');
    expect(content).toHaveClass('p-6', 'pt-0');
  });

  it('should render CardFooter', () => {
    render(
      <Card>
        <CardFooter>
          <button>Action Button</button>
        </CardFooter>
      </Card>
    );
    
    expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument();
    
    const footer = screen.getByRole('button').closest('div');
    expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0');
  });

  it('should render complete card structure', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Complete Card</CardTitle>
          <CardDescription>This is a complete card example</CardDescription>
        </CardHeader>
        <CardContent>
          <p>This is the main content of the card.</p>
        </CardContent>
        <CardFooter>
          <button>Action</button>
        </CardFooter>
      </Card>
    );
    
    expect(screen.getByText('Complete Card')).toBeInTheDocument();
    expect(screen.getByText('This is a complete card example')).toBeInTheDocument();
    expect(screen.getByText('This is the main content of the card.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('should accept custom className', () => {
    render(<Card className="custom-card">Custom Card</Card>);
    
    const card = screen.getByText('Custom Card').closest('div');
    expect(card).toHaveClass('custom-card');
  });

  it('should render CardTitle with proper heading level', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Heading Title</CardTitle>
        </CardHeader>
      </Card>
    );
    
    const title = screen.getByRole('heading', { level: 3 });
    expect(title).toHaveTextContent('Heading Title');
    expect(title).toHaveClass('text-2xl', 'font-semibold', 'leading-none', 'tracking-tight');
  });

  it('should render CardDescription with proper styling', () => {
    render(
      <Card>
        <CardHeader>
          <CardDescription>Description text</CardDescription>
        </CardHeader>
      </Card>
    );
    
    const description = screen.getByText('Description text');
    expect(description).toHaveClass('text-sm', 'text-muted-foreground');
  });

  it('should handle empty content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle></CardTitle>
          <CardDescription></CardDescription>
        </CardHeader>
        <CardContent></CardContent>
        <CardFooter></CardFooter>
      </Card>
    );
    
    const card = screen.getByRole('heading', { level: 3 }).closest('div');
    expect(card).toBeInTheDocument();
  });

  it('should render multiple cards', () => {
    render(
      <div>
        <Card>
          <CardContent>Card 1</CardContent>
        </Card>
        <Card>
          <CardContent>Card 2</CardContent>
        </Card>
      </div>
    );
    
    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
  });

  it('should forward refs correctly', () => {
    const ref = vi.fn();
    render(<Card ref={ref}>Ref Card</Card>);
    
    expect(ref).toHaveBeenCalled();
  });
});
