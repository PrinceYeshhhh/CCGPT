import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { NotFound } from '../NotFound';

describe('NotFound', () => {
  it('should render 404 message and home link', () => {
    render(
      <MemoryRouter>
        <NotFound />
      </MemoryRouter>
    );

    expect(screen.getByText('404 - Page Not Found')).toBeInTheDocument();
    expect(screen.getByText('The page you are looking for does not exist.')).toBeInTheDocument();
    
    const homeLink = screen.getByText('Go back home');
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/');
    expect(homeLink).toHaveClass('text-blue-600', 'hover:underline');
  });

  it('should have proper styling classes', () => {
    render(
      <MemoryRouter>
        <NotFound />
      </MemoryRouter>
    );

    const container = screen.getByText('404 - Page Not Found').closest('div');
    expect(container).toHaveClass(
      'min-h-[60vh]',
      'flex',
      'flex-col',
      'items-center',
      'justify-center',
      'text-center',
      'space-y-4'
    );
  });

  it('should have accessible heading structure', () => {
    render(
      <MemoryRouter>
        <NotFound />
      </MemoryRouter>
    );

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('404 - Page Not Found');
    expect(heading).toHaveClass('text-4xl', 'font-bold');
  });
});
