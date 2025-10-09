import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PaymentPopup } from '../PaymentPopup';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

const mockPlan = {
  id: 'pro',
  name: 'Pro Plan',
  price: 5000, // $50.00
  currency: 'usd',
  interval: 'month',
  features: [
    '5,000 queries/month',
    '100 documents',
    'Priority support',
  ],
};

describe('PaymentPopup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderPaymentPopup = (props = {}) => {
    const defaultProps = {
      isOpen: true,
      onClose: vi.fn(),
      plan: mockPlan,
      onSuccess: vi.fn(),
      ...props,
    };

    return render(<PaymentPopup {...defaultProps} />);
  };

  it('should render payment popup when open', () => {
    renderPaymentPopup();
    
    expect(screen.getByText('Complete Your Purchase')).toBeInTheDocument();
    expect(screen.getByText('Pro Plan')).toBeInTheDocument();
    expect(screen.getByText('$50.00')).toBeInTheDocument();
    expect(screen.getByText('per month')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    renderPaymentPopup({ isOpen: false });
    
    expect(screen.queryByText('Complete Your Purchase')).not.toBeInTheDocument();
  });

  it('should display plan features', () => {
    renderPaymentPopup();
    
    expect(screen.getByText('5,000 queries/month')).toBeInTheDocument();
    expect(screen.getByText('100 documents')).toBeInTheDocument();
    expect(screen.getByText('Priority support')).toBeInTheDocument();
  });

  it('should display payment methods', () => {
    renderPaymentPopup();
    
    expect(screen.getByText('Credit/Debit Card')).toBeInTheDocument();
    expect(screen.getByText('UPI')).toBeInTheDocument();
    expect(screen.getByText('Bank Transfer')).toBeInTheDocument();
  });

  it('should handle payment method selection', () => {
    renderPaymentPopup();
    
    const upiMethod = screen.getByText('UPI');
    fireEvent.click(upiMethod);
    
    expect(screen.getByText('UPI ID')).toBeInTheDocument();
  });

  it('should handle card payment method', () => {
    renderPaymentPopup();
    
    const cardMethod = screen.getByText('Credit/Debit Card');
    fireEvent.click(cardMethod);
    
    expect(screen.getByText('Card Number')).toBeInTheDocument();
    expect(screen.getByText('Expiry Date')).toBeInTheDocument();
    expect(screen.getByText('CVV')).toBeInTheDocument();
    expect(screen.getByText('Cardholder Name')).toBeInTheDocument();
  });

  it('should handle card details input', () => {
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    
    expect(cardNumberInput).toHaveValue('4111111111111111');
  });

  it('should handle UPI ID input', () => {
    renderPaymentPopup();
    
    const upiMethod = screen.getByText('UPI');
    fireEvent.click(upiMethod);
    
    const upiInput = screen.getByLabelText(/upi id/i);
    fireEvent.change(upiInput, { target: { value: 'test@upi' } });
    
    expect(upiInput).toHaveValue('test@upi');
  });

  it('should handle payment processing', async () => {
    mockApi.post.mockResolvedValue({ data: { success: true } });
    
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    const nameInput = screen.getByLabelText(/cardholder name/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '123' } });
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/billing/create-payment-intent', {
        plan_id: 'pro',
        payment_method: 'card',
        card_details: {
          number: '4111111111111111',
          expiry: '12/25',
          cvv: '123',
          name: 'John Doe',
        },
      });
    });
  });

  it('should handle payment success', async () => {
    const onSuccess = vi.fn();
    mockApi.post.mockResolvedValue({ data: { success: true } });
    
    renderPaymentPopup({ onSuccess });
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    const nameInput = screen.getByLabelText(/cardholder name/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '123' } });
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith({ success: true });
    });
  });

  it('should handle payment error', async () => {
    mockApi.post.mockRejectedValueOnce(new Error('Payment failed'));
    
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    const nameInput = screen.getByLabelText(/cardholder name/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '123' } });
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    await waitFor(() => {
      expect(screen.getByText('Payment failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('should handle close button', () => {
    const onClose = vi.fn();
    renderPaymentPopup({ onClose });
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should handle escape key to close', () => {
    const onClose = vi.fn();
    renderPaymentPopup({ onClose });
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should validate card number format', () => {
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    fireEvent.change(cardNumberInput, { target: { value: '123' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Please enter a valid card number')).toBeInTheDocument();
  });

  it('should validate expiry date format', () => {
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/2' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Please enter a valid expiry date (MM/YY)')).toBeInTheDocument();
  });

  it('should validate CVV format', () => {
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '12' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Please enter a valid CVV')).toBeInTheDocument();
  });

  it('should validate cardholder name', () => {
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '123' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Please enter cardholder name')).toBeInTheDocument();
  });

  it('should handle UPI payment', async () => {
    mockApi.post.mockResolvedValue({ data: { success: true } });
    
    renderPaymentPopup();
    
    const upiMethod = screen.getByText('UPI');
    fireEvent.click(upiMethod);
    
    const upiInput = screen.getByLabelText(/upi id/i);
    fireEvent.change(upiInput, { target: { value: 'test@upi' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/billing/create-payment-intent', {
        plan_id: 'pro',
        payment_method: 'upi',
        upi_id: 'test@upi',
      });
    });
  });

  it('should handle bank transfer payment', async () => {
    mockApi.post.mockResolvedValue({ data: { success: true } });
    
    renderPaymentPopup();
    
    const bankTransferMethod = screen.getByText('Bank Transfer');
    fireEvent.click(bankTransferMethod);
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/billing/create-payment-intent', {
        plan_id: 'pro',
        payment_method: 'bank_transfer',
      });
    });
  });

  it('should display security badges', () => {
    renderPaymentPopup();
    
    expect(screen.getByText('Secure Payment')).toBeInTheDocument();
    expect(screen.getByText('SSL Encrypted')).toBeInTheDocument();
  });

  it('should display payment summary', () => {
    renderPaymentPopup();
    
    expect(screen.getByText('Payment Summary')).toBeInTheDocument();
    expect(screen.getByText('Pro Plan')).toBeInTheDocument();
    expect(screen.getByText('$50.00')).toBeInTheDocument();
    expect(screen.getByText('per month')).toBeInTheDocument();
  });

  it('should handle loading state during payment', async () => {
    mockApi.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderPaymentPopup();
    
    const cardNumberInput = screen.getByLabelText(/card number/i);
    const expiryInput = screen.getByLabelText(/expiry date/i);
    const cvvInput = screen.getByLabelText(/cvv/i);
    const nameInput = screen.getByLabelText(/cardholder name/i);
    
    fireEvent.change(cardNumberInput, { target: { value: '4111111111111111' } });
    fireEvent.change(expiryInput, { target: { value: '12/25' } });
    fireEvent.change(cvvInput, { target: { value: '123' } });
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    const payButton = screen.getByText('Pay $50.00');
    fireEvent.click(payButton);
    
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(payButton).toBeDisabled();
  });
});
