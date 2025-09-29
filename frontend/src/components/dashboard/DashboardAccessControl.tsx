import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Lock, ArrowRight, Clock, CreditCard, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

interface DashboardAccessControlProps {
  children: React.ReactNode;
}

interface SubscriptionStatus {
  plan: string;
  status: string;
  isTrial: boolean;
  trialEnd?: string;
  currentPeriodEnd?: string;
  cancelAtPeriodEnd: boolean;
}

export function DashboardAccessControl({ children }: DashboardAccessControlProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    checkAccess();
  }, []);

  const checkAccess = async () => {
    try {
      setLoading(true);
      const response = await api.get('/billing/status');
      const billingInfo = response.data;
      
      setSubscription({
        plan: billingInfo.plan,
        status: billingInfo.status,
        isTrial: billingInfo.is_trial,
        trialEnd: billingInfo.trial_end,
        currentPeriodEnd: billingInfo.current_period_end,
        cancelAtPeriodEnd: billingInfo.cancel_at_period_end
      });

      // Check if user has access to dashboard
      const hasValidSubscription = 
        billingInfo.plan === 'free_trial' && billingInfo.status === 'trialing' ||
        billingInfo.plan === 'starter' && billingInfo.status === 'active' ||
        billingInfo.plan === 'pro' && billingInfo.status === 'active' ||
        billingInfo.plan === 'enterprise' && billingInfo.status === 'active' ||
        billingInfo.plan === 'white_label' && billingInfo.status === 'active';

      setHasAccess(hasValidSubscription);

      if (!hasValidSubscription) {
        // Check if trial has expired
        if (billingInfo.plan === 'free_trial' && billingInfo.status !== 'trialing') {
          toast.error('Your free trial has expired. Please upgrade to continue.');
        } else if (billingInfo.plan === 'free' || !billingInfo.plan) {
          // User has no subscription
        } else {
          toast.error('Your subscription is inactive. Please update your payment method.');
        }
      }

    } catch (error: any) {
      console.error('Failed to check subscription status:', error);
      // If we can't check subscription, allow access but show warning
      setHasAccess(true);
      toast.error('Unable to verify subscription status');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  const handleBilling = () => {
    navigate('/dashboard/billing');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Checking access...</p>
        </div>
      </div>
    );
  }

  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4">
              <Lock className="h-8 w-8 text-red-600" />
            </div>
            <CardTitle className="text-2xl font-bold">Access Restricted</CardTitle>
            <CardDescription>
              {subscription?.plan === 'free_trial' && subscription?.status !== 'trialing' 
                ? 'Your free trial has expired. Upgrade to continue using the dashboard.'
                : subscription?.plan === 'free' || !subscription?.plan
                ? 'You need an active subscription to access the dashboard.'
                : 'Your subscription is inactive. Please update your payment method.'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {subscription && (
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Current Plan:</span>
                  <Badge variant="outline">{subscription.plan}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  <Badge 
                    variant={subscription.status === 'active' ? 'default' : 'destructive'}
                  >
                    {subscription.status}
                  </Badge>
                </div>
                {subscription.isTrial && subscription.trialEnd && (
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm font-medium">Trial Ends:</span>
                    <span className="text-sm text-muted-foreground">
                      {new Date(subscription.trialEnd).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-3">
              <Button 
                onClick={handleUpgrade}
                className="w-full bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
                size="lg"
              >
                <ArrowRight className="mr-2 h-5 w-5" />
                {subscription?.plan === 'free_trial' ? 'Upgrade Now' : 'Choose a Plan'}
              </Button>
              
              {subscription?.plan !== 'free' && subscription?.plan !== 'free_trial' && (
                <Button 
                  onClick={handleBilling}
                  variant="outline"
                  className="w-full"
                >
                  <CreditCard className="mr-2 h-4 w-4" />
                  Manage Billing
                </Button>
              )}
            </div>

            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                Need help? Contact our support team for assistance.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
