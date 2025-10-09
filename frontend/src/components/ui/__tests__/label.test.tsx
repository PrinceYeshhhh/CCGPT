import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Label } from '../label';

describe('Label', () => {
  it('should render with default props', () => {
    render(<Label>Label Text</Label>);
    
    const label = screen.getByText('Label Text');
    expect(label).toBeInTheDocument();
    expect(label).toHaveClass('text-sm', 'font-medium', 'leading-none', 'peer-disabled:cursor-not-allowed', 'peer-disabled:opacity-70');
  });

  it('should render as label element by default', () => {
    render(<Label>Label</Label>);
    
    const label = screen.getByText('Label');
    expect(label.tagName).toBe('LABEL');
  });

  it('should render as different HTML elements', () => {
    const { rerender } = render(<Label asChild><span>Span Label</span></Label>);
    expect(screen.getByText('Span Label').tagName).toBe('SPAN');
    
    rerender(<Label asChild><div>Div Label</div></Label>);
    expect(screen.getByText('Div Label').tagName).toBe('DIV');
  });

  it('should accept custom className', () => {
    render(<Label className="custom-label">Custom</Label>);
    
    const label = screen.getByText('Custom');
    expect(label).toHaveClass('custom-label');
  });

  it('should associate with form controls', () => {
    render(
      <div>
        <Label htmlFor="input-id">Input Label</Label>
        <input id="input-id" type="text" />
      </div>
    );
    
    const label = screen.getByText('Input Label');
    const input = screen.getByRole('textbox');
    
    expect(label).toHaveAttribute('for', 'input-id');
    expect(input).toHaveAttribute('id', 'input-id');
  });

  it('should handle click events', () => {
    const handleClick = vi.fn();
    render(<Label onClick={handleClick}>Clickable Label</Label>);
    
    const label = screen.getByText('Clickable Label');
    fireEvent.click(label);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should render with different content types', () => {
    render(
      <div>
        <Label>Simple Text</Label>
        <Label>Required Field *</Label>
        <Label>With <strong>Bold</strong> Text</Label>
      </div>
    );
    
    expect(screen.getByText('Simple Text')).toBeInTheDocument();
    expect(screen.getByText('Required Field *')).toBeInTheDocument();
    expect(screen.getByText('With')).toBeInTheDocument();
    expect(screen.getByText('Bold')).toBeInTheDocument();
    expect(screen.getByText('Text')).toBeInTheDocument();
  });

  it('should handle empty content', () => {
    render(<Label></Label>);
    
    const label = screen.getByRole('generic');
    expect(label).toBeInTheDocument();
    expect(label).toHaveTextContent('');
  });

  it('should render multiple labels', () => {
    render(
      <div>
        <Label>Label 1</Label>
        <Label>Label 2</Label>
        <Label>Label 3</Label>
      </div>
    );
    
    expect(screen.getByText('Label 1')).toBeInTheDocument();
    expect(screen.getByText('Label 2')).toBeInTheDocument();
    expect(screen.getByText('Label 3')).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(<Label id="test-label">Accessible Label</Label>);
    
    const label = screen.getByText('Accessible Label');
    expect(label).toHaveAttribute('id', 'test-label');
  });

  it('should forward refs correctly', () => {
    const ref = vi.fn();
    render(<Label ref={ref}>Ref Label</Label>);
    
    expect(ref).toHaveBeenCalled();
  });

  it('should work with form controls', () => {
    render(
      <div>
        <Label htmlFor="checkbox-id">Checkbox Label</Label>
        <input id="checkbox-id" type="checkbox" />
      </div>
    );
    
    const label = screen.getByText('Checkbox Label');
    const checkbox = screen.getByRole('checkbox');
    
    expect(label).toHaveAttribute('for', 'checkbox-id');
    expect(checkbox).toHaveAttribute('id', 'checkbox-id');
  });

  it('should render with icons', () => {
    render(
      <Label>
        <span>📝</span>
        Form Label
      </Label>
    );
    
    const label = screen.getByText('Form Label');
    expect(label).toBeInTheDocument();
    expect(screen.getByText('📝')).toBeInTheDocument();
  });

  it('should handle disabled state styling', () => {
    render(
      <div>
        <Label>Normal Label</Label>
        <Label className="peer-disabled:opacity-50">Disabled Label</Label>
      </div>
    );
    
    const normalLabel = screen.getByText('Normal Label');
    const disabledLabel = screen.getByText('Disabled Label');
    
    expect(normalLabel).not.toHaveClass('peer-disabled:opacity-50');
    expect(disabledLabel).toHaveClass('peer-disabled:opacity-50');
  });
});
