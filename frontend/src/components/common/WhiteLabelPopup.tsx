import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Check,
  Loader2,
  X,
  Crown,
  Zap,
  Shield,
  Code
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface WhiteLabelPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (paymentData: any) => void;
}

export function WhiteLabelPopup({ isOpen, onClose, onSuccess }: WhiteLabelPopupProps) {
  const [whiteLabelPlan, setWhiteLabelPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchWhiteLabelPricing();
    }
  }, [isOpen]);

  const fetchWhiteLabelPricing = async () => {
    try {
      setLoading(true);
      const response = await api.get('/pricing/white-label');
      setWhiteLabelPlan(response.data);
    } catch (error) {
      console.error('Failed to fetch white label pricing:', error);
      toast.error('Failed to load white label pricing');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(price / 100);
  };

  const handlePurchase = async () => {
    if (!whiteLabelPlan) return;
    
    setIsProcessing(true);
    
    try {
      const checkoutData = {
        plan_tier: 'white_label',
        payment_method: 'stripe',
        success_url: `${window.location.origin}/dashboard/billing?success=true`,
        cancel_url: `${window.location.origin}/pricing?cancelled=true`,
        trial_days: 0
      };

      const response = await api.post('/billing/create-checkout-session', checkoutData);
      
      if (response.data.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = response.data.checkout_url;
      } else {
        toast.error('Failed to create checkout session');
      }
      
    } catch (error: any) {
      console.error('Purchase error:', error);
      toast.error(error.response?.data?.detail || 'Purchase failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading white label pricing...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!whiteLabelPlan) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <div className="text-center py-12">
            <h3 className="text-lg font-semibold mb-2">Unable to load pricing</h3>
            <p className="text-muted-foreground mb-4">There was an error loading white label pricing.</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Crown className="h-6 w-6 text-purple-600" />
              <span>White Label Solution</span>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center py-8 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 rounded-lg">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Complete White Label Solution
            </h2>
            <p className="text-lg text-muted-foreground mb-6 max-w-2xl mx-auto">
              Resell CustomerCareGPT under your own brand with full customization and unlimited usage.
            </p>
            <div className="text-4xl font-bold text-purple-600 mb-2">
              {formatPrice(whiteLabelPlan.price, whiteLabelPlan.currency)}
            </div>
            <div className="text-sm text-muted-foreground">One-time payment</div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-blue-500" />
                  <span>Unlimited Usage</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited queries
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited documents
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited storage
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited users
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-5 w-5 text-green-500" />
                  <span>White Label Features</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Custom domain support
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Your branding & logo
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Custom color schemes
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Remove all references to CustomerCareGPT
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Code className="h-5 w-5 text-orange-500" />
                  <span>Technical Access</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Source code access
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    API access
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Custom integrations
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Priority support
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Crown className="h-5 w-5 text-purple-500" />
                  <span>Business Benefits</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Resell to your clients
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Set your own pricing
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    Full control over the platform
                  </li>
                  <li className="flex items-center text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                    No monthly fees
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Purchase Section */}
          <Card className="border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950">
            <CardContent className="pt-6">
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-4">Ready to Go White Label?</h3>
                <p className="text-muted-foreground mb-6">
                  Get complete ownership and customization rights for your business.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button
                    onClick={handlePurchase}
                    disabled={isProcessing}
                    className="bg-gradient-to-br from-purple-600 to-pink-600 text-white border-0 hover:brightness-110 px-8 py-3 text-lg"
                  >
                    {isProcessing ? (
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    ) : null}
                    Purchase White Label - {formatPrice(whiteLabelPlan.price, whiteLabelPlan.currency)}
                  </Button>
                  <Button variant="outline" onClick={onClose}>
                    Learn More
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  One-time payment • Lifetime access • No recurring fees
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
