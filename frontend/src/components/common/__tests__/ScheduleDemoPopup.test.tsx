import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '@/test/test-utils';
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
    expect(screen.getByText('Book a personalized demo to see how CustomerCareGPT can help your business.')).toBeInTheDocument();
    expect(screen.getByLabelText('Name *')).toBeInTheDocument();
    expect(screen.getByLabelText('Organization')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
    expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
    expect(screen.getByLabelText('Preferred Date *')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /preferred time/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /timezone/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /company size/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /use case/i })).toBeInTheDocument();
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
    
    const xButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(xButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should update form data when inputs change', () => {
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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

  // Note: phone validation is not enforced in the current UI; skipping explicit invalid phone test

  it('should submit form successfully', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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
      expect(mockApi.post).toHaveBeenCalledWith('/support/schedule-demo', {
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
    
    expect(mockToast.success).toHaveBeenCalledWith("Demo request submitted successfully! We'll contact you soon to confirm the details.");
  });

  it('should show success state after submission', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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
      expect(screen.getByText('Demo Request Submitted!')).toBeInTheDocument();
      expect(screen.getByText("Thank you for your interest! We'll review your request and contact you within 24 hours to confirm your demo session.")).toBeInTheDocument();
    });
  });

  it('should handle API error', async () => {
    mockApi.post.mockRejectedValueOnce({ response: { data: { error: 'API Error' } } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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
      expect(screen.getByText('Submitting...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submitting.../i })).toBeDisabled();
    });
  });

  it('should reset form after successful submission', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { message: 'Demo scheduled successfully' } });
    
    render(<ScheduleDemoPopup isOpen={true} onClose={mockOnClose} />);
    
    const nameInput = screen.getByLabelText('Name *');
    const emailInput = screen.getByLabelText('Email Address *');
    const phoneInput = screen.getByLabelText('Phone Number');
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
    
    expect(screen.getByLabelText('Name *')).toHaveAttribute('required');
    expect(screen.getByLabelText('Email Address *')).toHaveAttribute('required');
    expect(screen.getByLabelText('Preferred Date *')).toHaveAttribute('required');
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
