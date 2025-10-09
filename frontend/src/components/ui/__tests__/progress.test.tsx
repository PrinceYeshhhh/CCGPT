import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Progress } from '../progress';

describe('Progress', () => {
  it('should render with default props', () => {
    render(<Progress value={50} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toBeInTheDocument();
    expect(progress).toHaveAttribute('aria-valuenow', '50');
    expect(progress).toHaveAttribute('aria-valuemin', '0');
    expect(progress).toHaveAttribute('aria-valuemax', '100');
  });

  it('should render with different values', () => {
    const { rerender } = render(<Progress value={0} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
    
    rerender(<Progress value={25} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '25');
    
    rerender(<Progress value={75} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '75');
    
    rerender(<Progress value={100} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('should handle undefined value', () => {
    render(<Progress value={undefined} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '0');
  });

  it('should accept custom className', () => {
    render(<Progress value={50} className="custom-progress" />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveClass('custom-progress');
  });

  it('should render progress bar with correct width', () => {
    render(<Progress value={60} />);
    
    const progressBar = screen.getByRole('progressbar');
    const indicator = progressBar.querySelector('[data-indicator]');
    
    expect(indicator).toHaveStyle('transform: translateX(-40%)');
  });

  it('should render progress bar with 0% width for 0 value', () => {
    render(<Progress value={0} />);
    
    const progressBar = screen.getByRole('progressbar');
    const indicator = progressBar.querySelector('[data-indicator]');
    
    expect(indicator).toHaveStyle('transform: translateX(-100%)');
  });

  it('should render progress bar with 100% width for 100 value', () => {
    render(<Progress value={100} />);
    
    const progressBar = screen.getByRole('progressbar');
    const indicator = progressBar.querySelector('[data-indicator]');
    
    expect(indicator).toHaveStyle('transform: translateX(0%)');
  });

  it('should have proper accessibility attributes', () => {
    render(<Progress value={75} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '75');
    expect(progress).toHaveAttribute('aria-valuemin', '0');
    expect(progress).toHaveAttribute('aria-valuemax', '100');
  });

  it('should render with custom max value', () => {
    render(<Progress value={50} max={200} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '50');
    expect(progress).toHaveAttribute('aria-valuemax', '200');
  });

  it('should handle negative values', () => {
    render(<Progress value={-10} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '-10');
  });

  it('should handle values greater than 100', () => {
    render(<Progress value={150} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '150');
  });

  it('should render multiple progress bars', () => {
    render(
      <div>
        <Progress value={25} data-testid="progress-1" />
        <Progress value={50} data-testid="progress-2" />
        <Progress value={75} data-testid="progress-3" />
      </div>
    );
    
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars).toHaveLength(3);
    expect(progressBars[0]).toHaveAttribute('aria-valuenow', '25');
    expect(progressBars[1]).toHaveAttribute('aria-valuenow', '50');
    expect(progressBars[2]).toHaveAttribute('aria-valuenow', '75');
  });

  it('should forward refs correctly', () => {
    const ref = vi.fn();
    render(<Progress value={50} ref={ref} />);
    
    expect(ref).toHaveBeenCalled();
  });

  it('should render with custom data attributes', () => {
    render(<Progress value={50} data-testid="custom-progress" />);
    
    const progress = screen.getByTestId('custom-progress');
    expect(progress).toBeInTheDocument();
  });

  it('should handle decimal values', () => {
    render(<Progress value={33.5} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '33.5');
  });

  it('should render with proper styling classes', () => {
    render(<Progress value={50} />);
    
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveClass('relative', 'h-4', 'w-full', 'overflow-hidden', 'rounded-full', 'bg-secondary');
  });
});
