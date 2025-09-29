import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, Star, Loader2 } from 'lucide-react';
import { PaymentPopup } from '@/components/common/PaymentPopup';
import { WhiteLabelPopup } from '@/components/common/WhiteLabelPopup';
import { TrialPopup } from '@/components/common/TrialPopup';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  stripe_price_id?: string;
  popular: boolean;
  trial_days: number;
}

export function Pricing() {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [showPaymentPopup, setShowPaymentPopup] = useState(false);
  const [showWhiteLabelPopup, setShowWhiteLabelPopup] = useState(false);
  const [showTrialPopup, setShowTrialPopup] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchPricingPlans();
  }, []);

  const fetchPricingPlans = async () => {
    try {
      const response = await api.get('/pricing/plans');
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error('Failed to fetch pricing plans:', error);
      toast.error('Failed to load pricing plans');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = (plan: PricingPlan) => {
    if (!isAuthenticated) {
      toast.error('Please sign in to continue');
      navigate('/login');
      return;
    }
    
    setSelectedPlan(plan);
    setShowPaymentPopup(true);
  };

  const handleStartTrial = () => {
    setShowTrialPopup(true);
  };

  const handlePaymentSuccess = (paymentData: any) => {
    toast.success('Payment successful! Welcome to your new plan.');
    setShowPaymentPopup(false);
    // Redirect to dashboard or billing page
    navigate('/dashboard/billing');
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(price / 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen py-20 bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading pricing plans...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-20 bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="flex justify-between items-center mb-6">
            <div></div>
            <h1 className="text-4xl md:text-5xl font-bold text-foreground">
            Simple, Transparent Pricing
          </h1>
            <Button 
              onClick={() => setShowWhiteLabelPopup(true)}
              className="bg-gradient-to-br from-purple-600 to-pink-600 text-white border-0 hover:brightness-110"
            >
              White Label
            </Button>
          </div>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Start with a 7-day free trial or choose a plan that fits your business needs.
          </p>
          <Button 
            onClick={handleStartTrial}
            className="bg-gradient-to-br from-green-600 to-blue-600 text-white border-0 hover:brightness-110 px-8 py-3 text-lg"
          >
            Start 7-Day Free Trial
          </Button>
          <p className="text-sm text-muted-foreground mt-2">
            100 queries • 1 document upload • No credit card required
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <Card 
              key={plan.id} 
              className={`relative transition-all duration-300 hover:shadow-xl ${
                plan.popular 
                  ? 'border-blue-500 shadow-xl scale-105 ring-2 ring-blue-500/20' 
                  : 'hover:border-blue-300 hover:-translate-y-1'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center shadow-lg">
                    <Star className="h-4 w-4 mr-1" />
                    Most Popular
                  </div>
                </div>
              )}
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                <div className="mt-4">
                  <span className="text-4xl font-bold">{formatPrice(plan.price, plan.currency)}</span>
                  <span className="text-muted-foreground">
                    {plan.interval === 'one_time' ? ' one-time' : `/${plan.interval}`}
                  </span>
                </div>
                <CardDescription className="mt-2">{plan.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full transition-all duration-200 bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110" 
                  variant={plan.popular ? "primary" : "outline"}
                  onClick={() => handleSubscribe(plan)}
                >
                  Choose Plan
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-8">
            Frequently Asked Questions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="text-left">
              <h3 className="font-semibold mb-2">Can I cancel anytime?</h3>
              <p className="text-muted-foreground">Yes, you can cancel your subscription at any time. No long-term contracts.</p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold mb-2">What happens after the trial?</h3>
              <p className="text-muted-foreground">After 7 days, you'll be charged for your selected plan. Cancel anytime during the trial.</p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold mb-2">Do you offer refunds?</h3>
              <p className="text-muted-foreground">Yes, we offer a 30-day money-back guarantee for all paid plans.</p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold mb-2">Can I upgrade my plan?</h3>
              <p className="text-muted-foreground">Absolutely! You can upgrade or downgrade your plan at any time from your dashboard.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Popup */}
      {selectedPlan && (
        <PaymentPopup
          isOpen={showPaymentPopup}
          onClose={() => setShowPaymentPopup(false)}
          plan={selectedPlan}
          onSuccess={handlePaymentSuccess}
        />
      )}

          {/* White Label Popup */}
          <WhiteLabelPopup
            isOpen={showWhiteLabelPopup}
            onClose={() => setShowWhiteLabelPopup(false)}
            onSuccess={handlePaymentSuccess}
          />

          {/* Trial Popup */}
          <TrialPopup
            isOpen={showTrialPopup}
            onClose={() => setShowTrialPopup(false)}
            onSuccess={(data) => {
              toast.success('7-day free trial started! You get 100 queries and can upload 1 document.');
              navigate('/dashboard');
            }}
          />
    </div>
  );
}