import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ScheduleDemoPopup } from '../ScheduleDemoPopup';
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

describe('ScheduleDemoPopup', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render when open', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByText('Schedule a Demo')).toBeInTheDocument();
    expect(screen.getByText('Book a personalized demo with our team')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Organization')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Phone')).toBeInTheDocument();
    expect(screen.getByLabelText('Preferred Date')).toBeInTheDocument();
    expect(screen.getByLabelText('Preferred Time')).toBeInTheDocument();
    expect(screen.getByLabelText('Timezone')).toBeInTheDocument();
    expect(screen.getByLabelText('Company Size')).toBeInTheDocument();
    expect(screen.getByLabelText('Use Case')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<ScheduleDemoPopup isOpen={false} onClose={mockOnClose} />);
    
    expect(screen.queryByText('Schedule a Demo')).not.toBeInTheDocument();
  });

  it('should close when close button is clicked', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should close when X button is clicked', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const xButton = screen.getByRole('button', { name: '' });
    fireEvent.click(xButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should update form data when inputs change', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const notesInput = screen.getByLabelText('Additional Notes');
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    fireEvent.change(notesInput, { target: { value: 'Test notes' } });
    
    expect(nameInput).toHaveValue('John Doe');
    expect(emailInput).toHaveValue('john@example.com');
    expect(phoneInput).toHaveValue('+1234567890');
    expect(dateInput).toHaveValue('2024-01-15');
    expect(notesInput).toHaveValue('Test notes');
  });

  it('should show validation error for empty required fields', async () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Please fill in all required fields');
    });
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('should show validation error for invalid email', async () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Please enter a valid email address');
    });
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('should show validation error for invalid phone', async () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: 'invalid-phone' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('Please enter a valid phone number');
    });
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  it('should submit form successfully', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    const companySizeSelect = screen.getByRole('combobox', { name: /company size/i });
    const useCaseSelect = screen.getByRole('combobox', { name: /use case/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    fireEvent.click(companySizeSelect);
    fireEvent.click(screen.getByText('11-50 employees'));
    
    fireEvent.click(useCaseSelect);
    fireEvent.click(screen.getByText('Customer Support Automation'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/demo/schedule', {
        name: 'John Doe',
        organization: '',
        email: 'john@example.com',
        phone: '+1234567890',
        preferredDate: '2024-01-15',
        preferredTime: '9:00 AM',
        timezone: 'UTC',
        companySize: '11-50 employees',
        useCase: 'Customer Support Automation',
        additionalNotes: ''
      });
    });
    
    expect(mockToast.success).toHaveBeenCalledWith('Demo scheduled successfully');
  });

  it('should show success state after submission', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Demo Scheduled Successfully!')).toBeInTheDocument();
      expect(screen.getByText('We will contact you soon to confirm the details.')).toBeInTheDocument();
    });
  });

  it('should handle API error', async () => {
    mockApi.post.mockRejectedValueOnce({ response: { data: { error: 'API Error' } } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith('API Error');
    });
  });

  it('should show loading state during submission', async () => {
    mockApi.post.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Scheduling...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /scheduling.../i })).toBeDisabled();
    });
  });

  it('should reset form after successful submission', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name');
    const emailInput = screen.getByLabelText('Email');
    const phoneInput = screen.getByLabelText('Phone');
    const dateInput = screen.getByLabelText('Preferred Date');
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(phoneInput, { target: { value: '+1234567890' } });
    fireEvent.change(dateInput, { target: { value: '2024-01-15' } });
    
    fireEvent.click(timeSelect);
    fireEvent.click(screen.getByText('9:00 AM'));
    
    const submitButton = screen.getByRole('button', { name: /schedule demo/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalled();
    });
    
    // Form should be reset
    expect(nameInput).toHaveValue('');
    expect(emailInput).toHaveValue('');
    expect(phoneInput).toHaveValue('');
    expect(dateInput).toHaveValue('');
  });

  it('should have proper accessibility attributes', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    expect(screen.getByLabelText('Name')).toHaveAttribute('required');
    expect(screen.getByLabelText('Email')).toHaveAttribute('required');
    expect(screen.getByLabelText('Phone')).toHaveAttribute('required');
    expect(screen.getByLabelText('Preferred Date')).toHaveAttribute('required');
    expect(screen.getByLabelText('Organization')).not.toHaveAttribute('required');
    expect(screen.getByLabelText('Additional Notes')).not.toHaveAttribute('required');
  });

  it('should display all time slots', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const timeSelect = screen.getByRole('combobox', { name: /preferred time/i });
    fireEvent.click(timeSelect);
    
    expect(screen.getByText('9:00 AM')).toBeInTheDocument();
    expect(screen.getByText('10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('11:00 AM')).toBeInTheDocument();
    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
    expect(screen.getByText('1:00 PM')).toBeInTheDocument();
    expect(screen.getByText('2:00 PM')).toBeInTheDocument();
    expect(screen.getByText('3:00 PM')).toBeInTheDocument();
    expect(screen.getByText('4:00 PM')).toBeInTheDocument();
    expect(screen.getByText('5:00 PM')).toBeInTheDocument();
  });

  it('should display all company sizes', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const companySizeSelect = screen.getByRole('combobox', { name: /company size/i });
    fireEvent.click(companySizeSelect);
    
    expect(screen.getByText('1-10 employees')).toBeInTheDocument();
    expect(screen.getByText('11-50 employees')).toBeInTheDocument();
    expect(screen.getByText('51-200 employees')).toBeInTheDocument();
    expect(screen.getByText('201-500 employees')).toBeInTheDocument();
    expect(screen.getByText('500+ employees')).toBeInTheDocument();
  });

  it('should display all use cases', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const useCaseSelect = screen.getByRole('combobox', { name: /use case/i });
    fireEvent.click(useCaseSelect);
    
    expect(screen.getByText('Customer Support Automation')).toBeInTheDocument();
    expect(screen.getByText('Sales Lead Qualification')).toBeInTheDocument();
    expect(screen.getByText('Technical Documentation')).toBeInTheDocument();
    expect(screen.getByText('FAQ Management')).toBeInTheDocument();
  });
});
