import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Register } from '../Register';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

describe('Register', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderRegister = () => {
    return render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
  };

  it('should render registration form', () => {
    renderRegister();
    
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByText('Get started with CustomerCareGPT')).toBeInTheDocument();
    expect(screen.getByText('Already have an account?')).toBeInTheDocument();
    expect(screen.getByText('Sign in')).toBeInTheDocument();
  });

  it('should display all form fields', () => {
    renderRegister();
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mobile/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/otp/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/domain/i)).toBeInTheDocument();
  });

  it('should handle form submission with valid data', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    renderRegister();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const mobileInput = screen.getByLabelText(/mobile/i);
    const otpInput = screen.getByLabelText(/otp/i);
    const organizationInput = screen.getByLabelText(/organization/i);
    const domainInput = screen.getByLabelText(/domain/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    fireEvent.change(domainInput, { target: { value: 'test.com' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'password123',
        full_name: 'testuser',
        business_name: 'Test Org',
        business_domain: 'test.com',
        mobile_phone: '1234567890',
        otp_code: '1234',
      });
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should show validation errors for invalid data', async () => {
    renderRegister();
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Username must be at least 3 characters')).toBeInTheDocument();
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
      expect(screen.getByText('Mobile number must be at least 10 digits')).toBeInTheDocument();
      expect(screen.getByText('OTP must be at least 4 digits')).toBeInTheDocument();
      expect(screen.getByText('Organization name must be at least 2 characters')).toBeInTheDocument();
    });
  });

  it('should show password mismatch error', async () => {
    renderRegister();
    
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'different123' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText("Passwords don't match")).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    mockApi.post.mockRejectedValueOnce(new Error('Registration failed'));
    
    renderRegister();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const mobileInput = screen.getByLabelText(/mobile/i);
    const otpInput = screen.getByLabelText(/otp/i);
    const organizationInput = screen.getByLabelText(/organization/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalled();
    });
  });

  it('should disable submit button when submitting', async () => {
    mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderRegister();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const mobileInput = screen.getByLabelText(/mobile/i);
    const otpInput = screen.getByLabelText(/otp/i);
    const organizationInput = screen.getByLabelText(/organization/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    expect(submitButton).toBeDisabled();
  });

  it('should show loading state during submission', async () => {
    mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderRegister();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const mobileInput = screen.getByLabelText(/mobile/i);
    const otpInput = screen.getByLabelText(/otp/i);
    const organizationInput = screen.getByLabelText(/organization/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    expect(screen.getByText('Creating Account...')).toBeInTheDocument();
  });

  it('should handle optional domain field', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    renderRegister();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    const mobileInput = screen.getByLabelText(/mobile/i);
    const otpInput = screen.getByLabelText(/otp/i);
    const organizationInput = screen.getByLabelText(/organization/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    // Leave domain empty
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'password123',
        full_name: 'testuser',
        business_name: 'Test Org',
        business_domain: '',
        mobile_phone: '1234567890',
        otp_code: '1234',
      });
    });
  });

  it('should display form icons', () => {
    renderRegister();
    
    // Check if icons are present (they should be in the DOM)
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mobile/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization/i)).toBeInTheDocument();
  });

  it('should have proper form structure', () => {
    renderRegister();
    
    expect(screen.getByRole('form')).toBeInTheDocument();
    expect(screen.getByText('Create Account')).toBeInTheDocument();
  });

  it('should handle email validation', async () => {
    renderRegister();
    
    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('should handle password length validation', async () => {
    renderRegister();
    
    const passwordInput = screen.getByLabelText(/password/i);
    fireEvent.change(passwordInput, { target: { value: '123' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    });
  });

  it('should handle mobile number validation', async () => {
    renderRegister();
    
    const mobileInput = screen.getByLabelText(/mobile/i);
    fireEvent.change(mobileInput, { target: { value: '123' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Mobile number must be at least 10 digits')).toBeInTheDocument();
    });
  });

  it('should handle OTP validation', async () => {
    renderRegister();
    
    const otpInput = screen.getByLabelText(/otp/i);
    fireEvent.change(otpInput, { target: { value: '12' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('OTP must be at least 4 digits')).toBeInTheDocument();
    });
  });

  it('should handle organization name validation', async () => {
    renderRegister();
    
    const organizationInput = screen.getByLabelText(/organization/i);
    fireEvent.change(organizationInput, { target: { value: 'A' } });
    
    const submitButton = screen.getByText('Create Account');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Organization name must be at least 2 characters')).toBeInTheDocument();
    });
  });
});
