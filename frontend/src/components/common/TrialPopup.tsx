import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { X, Loader2, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface TrialPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (data: any) => void;
}

export function TrialPopup({ isOpen, onClose, onSuccess }: TrialPopupProps) {
  const [formData, setFormData] = useState({
    email: '',
    mobile_phone: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.mobile_phone) {
      newErrors.mobile_phone = 'Mobile phone number is required';
    } else if (!/^\d{10,15}$/.test(formData.mobile_phone.replace(/\D/g, ''))) {
      newErrors.mobile_phone = 'Please enter a valid mobile phone number (10-15 digits)';
    }

    if (!formData.full_name) {
      newErrors.full_name = 'Full name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/pricing/start-trial', {
        plan_tier: 'free_trial',
        email: formData.email,
        mobile_phone: formData.mobile_phone.replace(/\D/g, ''), // Remove non-digits
        full_name: formData.full_name
      });

      if (response.data.success) {
        toast.success('7-day free trial started! You get 100 queries and can upload 1 document.');
        onSuccess(response.data);
        onClose();
      } else {
        toast.error(response.data.message);
      }
    } catch (error: any) {
      console.error('Trial error:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Failed to start trial. Please try again.';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="flex justify-between items-center">
            <CardTitle className="text-2xl font-bold">Start Free Trial</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription>
            Get 7 days free with 100 queries and 1 document upload
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email address"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="mobile_phone">Mobile Phone Number *</Label>
              <Input
                id="mobile_phone"
                type="tel"
                placeholder="Enter your mobile phone number"
                value={formData.mobile_phone}
                onChange={(e) => handleInputChange('mobile_phone', e.target.value)}
                className={errors.mobile_phone ? 'border-red-500' : ''}
              />
              {errors.mobile_phone && (
                <p className="text-sm text-red-500">{errors.mobile_phone}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name *</Label>
              <Input
                id="full_name"
                type="text"
                placeholder="Enter your full name"
                value={formData.full_name}
                onChange={(e) => handleInputChange('full_name', e.target.value)}
                className={errors.full_name ? 'border-red-500' : ''}
              />
              {errors.full_name && (
                <p className="text-sm text-red-500">{errors.full_name}</p>
              )}
            </div>

            <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
              <div className="flex items-start space-x-2">
                <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium">Trial Benefits:</p>
                  <ul className="mt-1 space-y-1">
                    <li>• 7 days completely free</li>
                    <li>• 100 queries included</li>
                    <li>• 1 document upload</li>
                    <li>• Full access to all features</li>
                    <li>• No credit card required</li>
                  </ul>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-br from-green-600 to-blue-600 text-white border-0 hover:brightness-110"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting Trial...
                </>
              ) : (
                'Start Free Trial'
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              By starting the trial, you agree to our Terms of Service and Privacy Policy.
              You can cancel anytime during the trial period.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
