import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  CreditCard, 
  Download, 
  Calendar, 
  AlertCircle,
  CheckCircle,
  ArrowUpRight,
  Receipt,
  Zap,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { api } from '@/lib/api';
import { PaymentPopup } from '@/components/common/PaymentPopup';
import { toast } from 'react-hot-toast';

interface BillingInfo {
  plan: string;
  status: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  usage: {
    queries_used: number;
    queries_limit: number;
    documents_used: number;
    documents_limit: number;
    storage_used: number;
    storage_limit: number;
  };
  billing_portal_url?: string;
  trial_end?: string;
  is_trial: boolean;
}

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  popular: boolean;
}

interface PaymentMethodInfo {
  id: string;
  type: string;
  last4?: string;
  brand?: string;
  exp_month?: number;
  exp_year?: number;
  is_default: boolean;
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created: string;
  invoice_pdf?: string;
  description?: string;
}

export function Billing() {
  const [billingInfo, setBillingInfo] = useState<BillingInfo | null>(null);
  const [pricingPlans, setPricingPlans] = useState<PricingPlan[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethodInfo[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [showPaymentPopup, setShowPaymentPopup] = useState(false);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setRefreshing(true);
      const [billingRes, pricingRes, paymentMethodsRes, invoicesRes] = await Promise.all([
        api.get('/billing/status'),
        api.get('/pricing/plans'),
        api.get('/billing/payment-methods'),
        api.get('/billing/invoices')
      ]);
      
      setBillingInfo(billingRes.data);
      setPricingPlans(pricingRes.data.plans || []);
      setPaymentMethods(paymentMethodsRes.data.payment_methods || []);
      setInvoices(invoicesRes.data?.invoices || []);
    } catch (error) {
      console.error('Failed to fetch billing data:', error);
      toast.error('Failed to load billing information. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(price / 100);
  };

  const handleUpgrade = (plan: PricingPlan) => {
    setSelectedPlan(plan);
    setShowPaymentPopup(true);
  };

  const handlePaymentSuccess = (paymentData: any) => {
    toast.success('Payment successful! Your plan has been upgraded.');
    setShowPaymentPopup(false);
    fetchBillingData(); // Refresh billing data
  };

  const downloadInvoice = (invoiceId: string) => {
    // Find the invoice to get the PDF URL
    const invoice = invoices.find(inv => inv.id === invoiceId);
    if (invoice?.invoice_pdf) {
      window.open(invoice.invoice_pdf, '_blank');
    } else {
      toast.error('Invoice PDF not available');
    }
  };

  const downloadAllInvoices = async () => {
    try {
      if (invoices.length === 0) {
        toast.error('No invoices available to download');
        return;
      }

      // Create a zip file with all invoices
      const response = await api.get('/billing/invoices/download-all', {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'all-invoices.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('All invoices downloaded successfully');
    } catch (error: any) {
      console.error('Download error:', error);
      toast.error(error.response?.data?.detail || 'Failed to download invoices');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading billing information...</span>
        </div>
      </div>
    );
  }

  if (!billingInfo) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Unable to load billing information</h3>
          <p className="text-muted-foreground mb-4">There was an error loading your billing details.</p>
          <Button onClick={fetchBillingData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Billing & Usage</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={fetchBillingData} disabled={refreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={downloadAllInvoices} aria-label="Download All Invoices">
            <Download className="mr-2 h-4 w-4" aria-hidden="true" />
            Download All Invoices
          </Button>
        </div>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <span>Current Plan</span>
                <Badge variant="secondary" className={`${
                  billingInfo.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                  billingInfo.status === 'trialing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                }`}>
                  {billingInfo.is_trial ? 'Trial' : billingInfo.status}
                </Badge>
                {billingInfo.is_trial && (
                  <Badge variant="outline" className="text-orange-600 border-orange-200">
                    {billingInfo.trial_end ? `Trial ends ${new Date(billingInfo.trial_end).toLocaleDateString()}` : 'Free Trial'}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                You're currently on the {billingInfo.plan.charAt(0).toUpperCase() + billingInfo.plan.slice(1)} plan
                {billingInfo.is_trial && ' (7-day free trial)'}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">
                {billingInfo.plan === 'free' || billingInfo.plan === 'free_trial' ? 'Free' : 
                 billingInfo.plan === 'starter' ? '$20' :
                 billingInfo.plan === 'pro' ? '$50' :
                 billingInfo.plan === 'enterprise' ? '$200' :
                 billingInfo.plan === 'white_label' ? '$999' : '$0'}
              </div>
              <div className="text-sm text-muted-foreground">
                {billingInfo.plan === 'free' || billingInfo.plan === 'free_trial' ? 'forever' : 
                 billingInfo.plan === 'white_label' ? 'one-time' : 'per month'}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center space-x-3">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Next billing date</p>
                <p className="text-sm text-muted-foreground">
                  {billingInfo.current_period_end ? 
                    new Date(billingInfo.current_period_end).toLocaleDateString() : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Payment method</p>
                <p className="text-sm text-muted-foreground">
                  {billingInfo.plan === 'free' || billingInfo.plan === 'free_trial' ? 'No payment required' : 
                   paymentMethods.length > 0 ? `•••• •••• •••• ${paymentMethods[0].last4}` : 'No payment method on file'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className={`h-5 w-5 ${
                billingInfo.status === 'active' ? 'text-green-500' :
                billingInfo.status === 'trialing' ? 'text-blue-500' :
                'text-gray-500'
              }`} />
              <div>
                <p className="text-sm font-medium">Status</p>
                <p className={`text-sm ${
                  billingInfo.status === 'active' ? 'text-green-600' :
                  billingInfo.status === 'trialing' ? 'text-blue-600' :
                  'text-gray-600'
                }`}>
                  {billingInfo.is_trial ? 'Free trial active' : 
                   billingInfo.status === 'active' ? 'Active subscription' :
                   'Inactive'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Queries</CardTitle>
            <CardDescription>Monthly query usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>{billingInfo.usage.queries_used.toLocaleString()} used</span>
                <span>{billingInfo.usage.queries_limit === -1 ? 'Unlimited' : billingInfo.usage.queries_limit.toLocaleString()} limit</span>
              </div>
              <Progress value={
                billingInfo.usage.queries_limit === -1 ? 0 : 
                (billingInfo.usage.queries_used / billingInfo.usage.queries_limit) * 100
              } />
              <p className="text-xs text-muted-foreground">
                {billingInfo.usage.queries_limit === -1 ? 'Unlimited queries' :
                 `${Math.round(((billingInfo.usage.queries_limit - billingInfo.usage.queries_used) / billingInfo.usage.queries_limit) * 100)}% remaining`}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Documents</CardTitle>
            <CardDescription>Uploaded documents</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>{billingInfo.usage.documents_used} used</span>
                <span>{billingInfo.usage.documents_limit === -1 ? 'Unlimited' : billingInfo.usage.documents_limit} limit</span>
              </div>
              <Progress value={
                billingInfo.usage.documents_limit === -1 ? 0 : 
                (billingInfo.usage.documents_used / billingInfo.usage.documents_limit) * 100
              } />
              <p className="text-xs text-muted-foreground">
                {billingInfo.usage.documents_limit === -1 ? 'Unlimited documents' :
                 `${billingInfo.usage.documents_limit - billingInfo.usage.documents_used} slots remaining`}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Storage</CardTitle>
            <CardDescription>Document storage used</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>{(billingInfo.usage.storage_used / (1024 * 1024 * 1024)).toFixed(1)} GB used</span>
                <span>{(billingInfo.usage.storage_limit / (1024 * 1024 * 1024)).toFixed(1)} GB limit</span>
              </div>
              <Progress value={(billingInfo.usage.storage_used / billingInfo.usage.storage_limit) * 100} />
              <p className="text-xs text-muted-foreground">
                {((billingInfo.usage.storage_limit - billingInfo.usage.storage_used) / (1024 * 1024 * 1024)).toFixed(1)} GB remaining
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upgrade Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Upgrade Your Plan</CardTitle>
          <CardDescription>
            Choose a plan that fits your growing business needs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {pricingPlans.map((plan) => {
              const isCurrentPlan = plan.id === billingInfo.plan;
              return (
                <div 
                  key={plan.id}
                  className={`relative p-6 rounded-lg border-2 transition-all ${
                    isCurrentPlan 
                      ? 'border-primary bg-primary/5' 
                      : 'border-muted hover:border-primary/50'
                  }`}
                >
                  {isCurrentPlan && (
                    <Badge className="absolute -top-2 left-4 bg-primary">
                      Current Plan
                    </Badge>
                  )}
                  {plan.popular && !isCurrentPlan && (
                    <Badge className="absolute -top-2 right-4 bg-blue-500">
                      Popular
                    </Badge>
                  )}
                  <div className="text-center mb-4">
                    <h3 className="text-lg font-semibold">{plan.name}</h3>
                    <div className="text-2xl font-bold mt-2">
                      {formatPrice(plan.price, plan.currency)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {plan.interval === 'one_time' ? 'one-time' : `per ${plan.interval}`}
                    </div>
                  </div>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className={`w-full ${
                      !isCurrentPlan ? 'bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110' : ''
                    }`} 
                    variant={isCurrentPlan ? "outline" : "default"}
                    onClick={() => handleUpgrade(plan)}
                    disabled={isCurrentPlan}
                  >
                    {isCurrentPlan ? 'Current Plan' : 'Upgrade'}
                    {!isCurrentPlan && <ArrowUpRight className="ml-2 h-4 w-4" />}
                  </Button>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
          <CardDescription>Manage your payment information</CardDescription>
        </CardHeader>
        <CardContent>
          {paymentMethods.length > 0 ? (
            <div className="space-y-3">
              {paymentMethods.map((method) => (
                <div key={method.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded flex items-center justify-center">
                      <CreditCard className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {method.brand?.toUpperCase()} •••• •••• •••• {method.last4}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Expires {method.exp_month}/{method.exp_year}
                        {method.is_default && ' • Default'}
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    Update
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Payment Method</h3>
              <p className="text-muted-foreground mb-4">
                {billingInfo.plan === 'free' || billingInfo.plan === 'free_trial' 
                  ? 'No payment method required for your current plan'
                  : 'Add a payment method to manage your subscription'
                }
              </p>
              {billingInfo.plan !== 'free' && billingInfo.plan !== 'free_trial' && (
                <Button>
                  Add Payment Method
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>Download your previous invoices</CardDescription>
        </CardHeader>
        <CardContent>
          {invoices.length > 0 ? (
            <div className="space-y-3">
              {invoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Receipt className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{invoice.description || `${invoice.id} Invoice`}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(invoice.created).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge variant={invoice.status === 'paid' ? 'default' : 'secondary'}>
                      {invoice.status}
                    </Badge>
                    <span className="font-medium">
                      {formatPrice(invoice.amount, invoice.currency)}
                    </span>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      aria-label={`Download invoice ${invoice.id}`}
                      onClick={() => downloadInvoice(invoice.id)}
                    >
                      <Download className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Receipt className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Invoices</h3>
              <p className="text-muted-foreground">
                {billingInfo.plan === 'free' || billingInfo.plan === 'free_trial' 
                  ? 'No invoices available for your current plan'
                  : 'Your billing history will appear here once you have active subscriptions'
                }
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Alert */}
      {billingInfo.usage.queries_limit !== -1 && (billingInfo.usage.queries_used / billingInfo.usage.queries_limit) > 0.8 && (
        <Card className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-orange-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-orange-800 dark:text-orange-200">
                  High Usage Alert
                </h3>
                <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
                  You've used {Math.round((billingInfo.usage.queries_used / billingInfo.usage.queries_limit) * 100)}% of your monthly query limit. 
                  Consider upgrading to avoid service interruption.
                </p>
                <Button size="sm" className="mt-3" onClick={() => {
                  const enterprisePlan = pricingPlans.find(p => p.id === 'enterprise');
                  if (enterprisePlan) handleUpgrade(enterprisePlan);
                }}>
                  <Zap className="mr-2 h-4 w-4" />
                  Upgrade Now
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payment Popup */}
      {selectedPlan && (
        <PaymentPopup
          isOpen={showPaymentPopup}
          onClose={() => setShowPaymentPopup(false)}
          plan={selectedPlan}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
}