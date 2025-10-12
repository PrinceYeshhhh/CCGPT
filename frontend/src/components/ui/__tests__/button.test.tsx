import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../button';

describe('Button', () => {
  it('should render with default props', () => {
    act(() => {
      render(<Button>Click me</Button>);
    });
    
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-primary', 'text-primary-foreground');
  });

  it('should render with different variants', () => {
    const { rerender } = render(<Button variant="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary', 'text-primary-foreground');
    
    act(() => {
      rerender(<Button variant="destructive">Destructive</Button>);
    });
    expect(screen.getByRole('button')).toHaveClass('bg-destructive', 'text-destructive-foreground');
    
    act(() => {
      rerender(<Button variant="outline">Outline</Button>);
    });
    expect(screen.getByRole('button')).toHaveClass('border', 'border-input');
    
    act(() => {
      rerender(<Button variant="secondary">Secondary</Button>);
    });
    expect(screen.getByRole('button')).toHaveClass('bg-secondary', 'text-secondary-foreground');
    
    act(() => {
      rerender(<Button variant="ghost">Ghost</Button>);
    });
    expect(screen.getByRole('button')).toHaveClass('hover:bg-accent', 'hover:text-accent-foreground');
    
    act(() => {
      rerender(<Button variant="link">Link</Button>);
    });
    expect(screen.getByRole('button')).toHaveClass('text-primary', 'underline-offset-4');
  });

  it('should render with different sizes', () => {
    const { rerender } = render(<Button size="default">Default</Button>);
    // Default size has padding classes regardless of breakpoint
    expect(screen.getByRole('button')).toHaveClass('px-4', 'py-2');
    
    rerender(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('rounded-md', 'px-3');
    
    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('rounded-md', 'px-8');
    
    rerender(<Button size="icon">Icon</Button>);
    // Icon size guarantees square shape with width class present
    expect(screen.getByRole('button').className).toMatch(/w-(10|12)/);
  });

  it('should handle click events', () => {
    const handleClick = vi.fn();
    act(() => {
      render(<Button onClick={handleClick}>Click me</Button>);
    });
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    act(() => {
      render(<Button disabled>Disabled</Button>);
    });
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('disabled:pointer-events-none', 'disabled:opacity-50');
  });

  it('should not call onClick when disabled', () => {
    const handleClick = vi.fn();
    act(() => {
      render(<Button disabled onClick={handleClick}>Disabled</Button>);
    });
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should render as different HTML elements', () => {
    const { rerender } = render(<Button asChild><a href="/test">Link</a></Button>);
    expect(screen.getByRole('link')).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', '/test');
    
    act(() => {
      rerender(<Button asChild><span>Span</span></Button>);
    });
    expect(screen.getByText('Span')).toBeInTheDocument();
  });

  it('should accept custom className', () => {
    act(() => {
      render(<Button className="custom-class">Custom</Button>);
    });
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('should forward ref', () => {
    const ref = vi.fn();
    act(() => {
      render(<Button ref={ref}>Ref test</Button>);
    });
    
    expect(ref).toHaveBeenCalled();
  });

  it('should have proper accessibility attributes', () => {
    act(() => {
      render(<Button aria-label="Custom label">Button</Button>);
    });
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Custom label');
  });

  it('should support loading state', () => {
    act(() => {
      render(<Button disabled>Loading...</Button>);
    });
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('Loading...');
  });

  it('should render with icon and text', () => {
    act(() => {
      render(
        <Button>
          <span>Icon</span>
          Button Text
        </Button>
      );
    });
    
    const button = screen.getByRole('button');
    expect(button).toHaveTextContent('Icon');
    expect(button).toHaveTextContent('Button Text');
  });
});
