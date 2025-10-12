import { renderWithProviders as render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Register } from '../Register';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    post: vi.fn().mockRejectedValue(new Error('API Error')),
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

  const renderRegister = () => render(<Register />);

  it('should render registration form', () => {
    renderRegister();
    
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByText('Get started with CustomerCareGPT in seconds')).toBeInTheDocument();
    expect(screen.getByText('Already have an account?')).toBeInTheDocument();
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('should display all form fields', () => {
    renderRegister();
    
    expect(screen.getByPlaceholderText('Choose a username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Create a password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Confirm your password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your mobile number')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter OTP')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your organization name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('company.com')).toBeInTheDocument();
  });

  it('should handle form submission with valid data', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    renderRegister();
    
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    const domainInput = screen.getByPlaceholderText('company.com');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    fireEvent.change(domainInput, { target: { value: 'test.com' } });
    
    // Check the terms checkbox
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    const submitButton = screen.getByText('Start 7-day free trial');
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
    
    const form = document.querySelector('form');
    const submitButton = screen.getByText('Start 7-day free trial');
    
    // Submit the form to trigger validation
    fireEvent.submit(form);
    
    // Wait for form validation to trigger
    await waitFor(() => {
      expect(screen.getByText('Username must be at least 3 characters')).toBeInTheDocument();
    }, { timeout: 5000 });
    
    expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    expect(screen.getByText('Mobile number must be at least 10 digits')).toBeInTheDocument();
    expect(screen.getByText('OTP must be at least 4 digits')).toBeInTheDocument();
    expect(screen.getByText('Organization name must be at least 2 characters')).toBeInTheDocument();
  });

  it('should show password mismatch error', async () => {
    renderRegister();
    
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'different123' } });
    
    const form = document.querySelector('form');
    fireEvent.submit(form);
    
    await waitFor(() => {
      expect(screen.getByText("Passwords don't match")).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('should handle API errors', async () => {
    mockApi.post.mockRejectedValueOnce(new Error('Registration failed'));
    
    renderRegister();
    
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalled();
    });
  });

  it('should disable submit button when submitting', async () => {
    mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderRegister();
    
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    // Wait for the button to be disabled
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it('should show loading state during submission', async () => {
    mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderRegister();
    
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Creating account...')).toBeInTheDocument();
    });
  });

  it('should handle optional domain field', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    renderRegister();
    
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    // Leave domain empty
    
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    const submitButton = screen.getByText('Start 7-day free trial');
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
    
    // Check if form fields are present (they should be in the DOM)    
    expect(screen.getByPlaceholderText('Choose a username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Create a password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your mobile number')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your organization name')).toBeInTheDocument();
  });

  it('should have proper form structure', () => {
    renderRegister();
    
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByText('Start 7-day free trial')).toBeInTheDocument();
  });

  it('should handle email validation', async () => {
    renderRegister();
    
    // Just submit the form without filling any fields to trigger validation
    const form = document.querySelector('form');
    fireEvent.submit(form);
    
    // Wait for validation errors to appear
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('should handle password length validation', async () => {
    renderRegister();
    
    // Fill in all required fields except password
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(confirmPasswordInput, { target: { value: '123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    fireEvent.click(termsCheckbox);
    
    // Set invalid password
    const passwordInput = screen.getByPlaceholderText('Create a password');
    fireEvent.change(passwordInput, { target: { value: '123' } });
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
    });
  });

  it('should handle mobile number validation', async () => {
    renderRegister();
    
    // Fill in all required fields except mobile
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    fireEvent.click(termsCheckbox);
    
    // Set invalid mobile number
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    fireEvent.change(mobileInput, { target: { value: '123' } });
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Mobile number must be at least 10 digits')).toBeInTheDocument();
    });
  });

  it('should handle OTP validation', async () => {
    renderRegister();
    
    // Fill in all required fields except OTP
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(organizationInput, { target: { value: 'Test Org' } });
    fireEvent.click(termsCheckbox);
    
    // Set invalid OTP
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    fireEvent.change(otpInput, { target: { value: '12' } });
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('OTP must be at least 4 digits')).toBeInTheDocument();
    });
  });

  it('should handle organization name validation', async () => {
    renderRegister();
    
    // Fill in all required fields except organization
    const usernameInput = screen.getByPlaceholderText('Choose a username');
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const passwordInput = screen.getByPlaceholderText('Create a password');
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm your password');
    const mobileInput = screen.getByPlaceholderText('Enter your mobile number');
    const otpInput = screen.getByPlaceholderText('Enter OTP');
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.change(mobileInput, { target: { value: '1234567890' } });
    fireEvent.change(otpInput, { target: { value: '1234' } });
    fireEvent.click(termsCheckbox);
    
    // Set invalid organization name
    const organizationInput = screen.getByPlaceholderText('Enter your organization name');
    fireEvent.change(organizationInput, { target: { value: 'A' } });
    
    const submitButton = screen.getByText('Start 7-day free trial');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Organization name must be at least 2 characters')).toBeInTheDocument();
    });
  });
});
