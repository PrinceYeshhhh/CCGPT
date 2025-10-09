import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge } from '../badge';

describe('Badge', () => {
  it('should render with default props', () => {
    render(<Badge>Default Badge</Badge>);
    
    const badge = screen.getByText('Default Badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('inline-flex', 'items-center', 'rounded-full', 'border', 'px-2.5', 'py-0.5', 'text-xs', 'font-semibold', 'transition-colors', 'focus:outline-none', 'focus:ring-2', 'focus:ring-ring', 'focus:ring-offset-2', 'border-transparent', 'bg-primary', 'text-primary-foreground', 'hover:bg-primary/80');
  });

  it('should render with different variants', () => {
    const { rerender } = render(<Badge variant="default">Default</Badge>);
    expect(screen.getByText('Default')).toHaveClass('bg-primary', 'text-primary-foreground');
    
    rerender(<Badge variant="secondary">Secondary</Badge>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-secondary', 'text-secondary-foreground');
    
    rerender(<Badge variant="destructive">Destructive</Badge>);
    expect(screen.getByText('Destructive')).toHaveClass('bg-destructive', 'text-destructive-foreground');
    
    rerender(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText('Outline')).toHaveClass('text-foreground');
  });

  it('should accept custom className', () => {
    render(<Badge className="custom-badge">Custom</Badge>);
    
    const badge = screen.getByText('Custom');
    expect(badge).toHaveClass('custom-badge');
  });

  it('should render with different content types', () => {
    render(
      <div>
        <Badge>Text Badge</Badge>
        <Badge>123</Badge>
        <Badge>Status</Badge>
      </div>
    );
    
    expect(screen.getByText('Text Badge')).toBeInTheDocument();
    expect(screen.getByText('123')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('should render with icons', () => {
    render(
      <Badge>
        <span>🔔</span>
        Notifications
      </Badge>
    );
    
    const badge = screen.getByText('Notifications');
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('🔔')).toBeInTheDocument();
  });

  it('should handle empty content', () => {
    render(<Badge></Badge>);
    
    const badge = screen.getByRole('generic');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('');
  });

  it('should render multiple badges', () => {
    render(
      <div>
        <Badge variant="default">Badge 1</Badge>
        <Badge variant="secondary">Badge 2</Badge>
        <Badge variant="destructive">Badge 3</Badge>
      </div>
    );
    
    expect(screen.getByText('Badge 1')).toBeInTheDocument();
    expect(screen.getByText('Badge 2')).toBeInTheDocument();
    expect(screen.getByText('Badge 3')).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(<Badge role="status">Active</Badge>);
    
    const badge = screen.getByRole('status');
    expect(badge).toHaveTextContent('Active');
  });

  it('should forward refs correctly', () => {
    const ref = vi.fn();
    render(<Badge ref={ref}>Ref Badge</Badge>);
    
    expect(ref).toHaveBeenCalled();
  });

  it('should render with different sizes using className', () => {
    render(<Badge className="text-sm px-3 py-1">Large Badge</Badge>);
    
    const badge = screen.getByText('Large Badge');
    expect(badge).toHaveClass('text-sm', 'px-3', 'py-1');
  });

  it('should render with custom colors using className', () => {
    render(<Badge className="bg-green-500 text-white">Success</Badge>);
    
    const badge = screen.getByText('Success');
    expect(badge).toHaveClass('bg-green-500', 'text-white');
  });
});
