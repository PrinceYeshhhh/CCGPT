import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  CreditCard, 
  Smartphone, 
  Building2, 
  Check,
  Loader2,
  X
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface PaymentPopupProps {
  isOpen: boolean;
  onClose: () => void;
  plan: {
    id: string;
    name: string;
    price: number;
    currency: string;
    interval: string;
    features: string[];
  };
  onSuccess?: (paymentData: any) => void;
}

type PaymentMethod = 'card' | 'stripe' | 'upi' | 'bank_transfer';

export function PaymentPopup({ isOpen, onClose, plan, onSuccess }: PaymentPopupProps) {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('card');
  const [isProcessing, setIsProcessing] = useState(false);
  const [cardDetails, setCardDetails] = useState({
    number: '',
    expiry: '',
    cvv: '',
    name: ''
  });
  const [upiId, setUpiId] = useState('');

  const paymentMethods = [
    {
      id: 'card' as PaymentMethod,
      name: 'Credit/Debit Card',
      icon: CreditCard,
      description: 'Pay with Visa, Mastercard, or American Express',
      popular: true
    },
    {
      id: 'stripe' as PaymentMethod,
      name: 'Stripe Checkout',
      icon: Building2,
      description: 'Secure payment processing by Stripe',
      popular: false
    },
    {
      id: 'upi' as PaymentMethod,
      name: 'UPI (India)',
      icon: Smartphone,
      description: 'Pay using UPI ID or QR code',
      popular: false
    }
  ];

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(price / 100);
  };

  const handlePayment = async () => {
    setIsProcessing(true);
    
    try {
      const checkoutData = {
        plan_tier: plan.id,
        payment_method: selectedMethod,
        success_url: `${window.location.origin}/dashboard/billing?success=true`,
        cancel_url: `${window.location.origin}/pricing?cancelled=true`,
        trial_days: 7
      };

      const response = await api.post('/billing/create-checkout-session', checkoutData);
      
      if (response.data.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = response.data.checkout_url;
      } else if (response.data.payment_intent_id) {
        // Handle direct payment (for card payments)
        toast.success('Payment processed successfully!');
        onSuccess?.(response.data);
        onClose();
      } else if (response.data.upi_payment_url) {
        // Handle UPI payment
        window.open(response.data.upi_payment_url, '_blank');
        toast.success('UPI payment initiated. Please complete the payment.');
      }
      
    } catch (error: any) {
      console.error('Payment error:', error);
      toast.error(error.response?.data?.detail || 'Payment failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStartTrial = async () => {
    setIsProcessing(true);
    
    try {
      const trialData = {
        plan_tier: plan.id,
        email: 'user@example.com', // This would come from auth context
        full_name: 'User Name' // This would come from auth context
      };

      const response = await api.post('/pricing/start-trial', trialData);
      
      if (response.data.success) {
        toast.success('7-day free trial started!');
        onSuccess?.(response.data);
        onClose();
      } else {
        toast.error(response.data.message);
      }
      
    } catch (error: any) {
      console.error('Trial error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start trial. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Complete Your Purchase</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Plan Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{plan.name} Plan</span>
                <Badge variant="secondary">7-Day Free Trial</Badge>
              </CardTitle>
              <CardDescription>
                {plan.interval === 'one_time' ? 'One-time payment' : `Billed ${plan.interval}ly`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Price</span>
                  <span>{formatPrice(plan.price, plan.currency)}</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {plan.interval === 'one_time' ? 'One-time payment' : `After 7-day free trial`}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Methods */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Choose Payment Method</h3>
            <div className="grid grid-cols-1 gap-3">
              {paymentMethods.map((method) => {
                const Icon = method.icon;
                return (
                  <Card 
                    key={method.id}
                    className={`cursor-pointer transition-all ${
                      selectedMethod === method.id 
                        ? 'ring-2 ring-primary border-primary' 
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedMethod(method.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${
                          selectedMethod === method.id ? 'bg-primary text-primary-foreground' : 'bg-muted'
                        }`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium">{method.name}</h4>
                            {method.popular && (
                              <Badge variant="secondary" className="text-xs">Popular</Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{method.description}</p>
                        </div>
                        {selectedMethod === method.id && (
                          <Check className="h-5 w-5 text-primary" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* Payment Form */}
          {selectedMethod === 'card' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Card Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <Label htmlFor="cardNumber">Card Number</Label>
                  <Input
                    id="cardNumber"
                    placeholder="1234 5678 9012 3456"
                    value={cardDetails.number}
                    onChange={(e) => setCardDetails({...cardDetails, number: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="expiry">Expiry Date</Label>
                  <Input
                    id="expiry"
                    placeholder="MM/YY"
                    value={cardDetails.expiry}
                    onChange={(e) => setCardDetails({...cardDetails, expiry: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="cvv">CVV</Label>
                  <Input
                    id="cvv"
                    placeholder="123"
                    value={cardDetails.cvv}
                    onChange={(e) => setCardDetails({...cardDetails, cvv: e.target.value})}
                  />
                </div>
                <div className="col-span-2">
                  <Label htmlFor="cardName">Cardholder Name</Label>
                  <Input
                    id="cardName"
                    placeholder="John Doe"
                    value={cardDetails.name}
                    onChange={(e) => setCardDetails({...cardDetails, name: e.target.value})}
                  />
                </div>
              </div>
            </div>
          )}

          {selectedMethod === 'upi' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">UPI Details</h3>
              <div>
                <Label htmlFor="upiId">UPI ID</Label>
                <Input
                  id="upiId"
                  placeholder="yourname@paytm"
                  value={upiId}
                  onChange={(e) => setUpiId(e.target.value)}
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Enter your UPI ID to receive payment request
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4 border-t">
            <Button
              variant="outline"
              onClick={handleStartTrial}
              disabled={isProcessing}
              className="flex-1"
            >
              {isProcessing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Start 7-Day Free Trial
            </Button>
            <Button
              onClick={handlePayment}
              disabled={isProcessing}
              className="flex-1 bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
            >
              {isProcessing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Pay Now
            </Button>
          </div>

          {/* Security Notice */}
          <div className="text-center text-sm text-muted-foreground">
            <p>🔒 Your payment information is secure and encrypted</p>
            <p>You can cancel your subscription anytime from your dashboard</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
