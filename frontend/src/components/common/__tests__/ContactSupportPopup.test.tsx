import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ContactSupportPopup } from '../ContactSupportPopup';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);
const mockToast = vi.mocked(toast);

describe('ContactSupportPopup', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render when open', () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByText('Contact Support')).toBeInTheDocument();
    expect(screen.getByText('Get help from our support team')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Organization')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Question')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<ContactSupportPopup isOpen={false} onClose={mockOnClose} />);
    
    expect(screen.queryByText('Contact Support')).not.toBeInTheDocument();
  });

  it('should close when close button is clicked', () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should close when X button is clicked', () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const xButton = screen.getByRole('button', { name: '' });
    fireEvent.click(xButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should update form data when inputs change', () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    expect(nameInput).toHaveValue('John Doe');
    expect(emailInput).toHaveValue('john@example.com');
    expect(questionInput).toHaveValue('Test question');
  });

  it('should show validation error for empty required fields', async () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Please fill in all required fields');
    });
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('should show validation error for invalid email', async () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Please enter a valid email address');
    });
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('should submit form successfully', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Message sent successfully' } });
    
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/support/contact', {
        name: 'John Doe',
        organization: '',
        email: 'john@example.com',
        question: 'Test question'
      });
    });
    
    expect(mockToast.success).toHaveBeenCalledWith('Message sent successfully');
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should handle API error', async () => {
    mockApi.post.mockRejectedValueOnce({ response: { data: { error: 'API Error' } } });
    
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('API Error');
    });
    
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should show loading state during submission', async () => {
    mockApi.post.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sending.../i })).toBeDisabled();
    });
  });

  it('should reset form after successful submission', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Message sent successfully' } });
    
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalled();
    });
    
    // Form should be reset
    expect(nameInput).toHaveValue('');
    expect(emailInput).toHaveValue('');
    expect(questionInput).toHaveValue('');
  });

  it('should handle organization field as optional', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Message sent successfully' } });
    
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const questionInput = screen.getByLabelText('Question');
    const organizationInput = screen.getByLabelText('Organization');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(questionInput, { target: { value: 'Test question' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const submitButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/support/contact', {
        name: 'John Doe',
        organization: 'Test Org',
        email: 'john@example.com',
        question: 'Test question'
      });
    });
  });

  it('should have proper accessibility attributes', () => {
    render(<ContactSupportPopup isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByLabelText('Name')).toHaveAttribute('required');
    expect(screen.getByLabelText('Email')).toHaveAttribute('required');
    expect(screen.getByLabelText('Question')).toHaveAttribute('required');
    expect(screen.getByLabelText('Organization')).not.toHaveAttribute('required');
  });
});
