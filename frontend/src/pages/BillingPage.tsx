import { useState } from 'react'
import { useQuery } from 'react-query'
import { CreditCard, Check, X, AlertCircle, ExternalLink } from 'lucide-react'
import { api } from '../lib/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

interface BillingInfo {
  plan: 'free' | 'pro' | 'enterprise'
  status: 'active' | 'canceled' | 'past_due'
  current_period_end: string
  cancel_at_period_end: boolean
  usage: {
    queries_used: number
    queries_limit: number
    documents_used: number
    documents_limit: number
    storage_used: number
    storage_limit: number
  }
  billing_portal_url?: string
}

const plans = {
  free: {
    name: 'Free',
    price: 0,
    features: [
      'Up to 100 queries/month',
      'Up to 5 documents',
      'Basic analytics',
      'Email support'
    ],
    limits: {
      queries: 100,
      documents: 5,
      storage: 100 // MB
    }
  },
  pro: {
    name: 'Pro',
    price: 29,
    features: [
      'Up to 10,000 queries/month',
      'Unlimited documents',
      'Advanced analytics',
      'Priority support',
      'Custom branding',
      'API access'
    ],
    limits: {
      queries: 10000,
      documents: -1, // unlimited
      storage: 1000 // MB
    }
  },
  enterprise: {
    name: 'Enterprise',
    price: 99,
    features: [
      'Unlimited queries',
      'Unlimited documents',
      'Full analytics suite',
      '24/7 phone support',
      'Custom integrations',
      'Dedicated account manager',
      'SLA guarantee'
    ],
    limits: {
      queries: -1, // unlimited
      documents: -1, // unlimited
      storage: 10000 // MB
    }
  }
}

export function BillingPage() {
  const [isLoading, setIsLoading] = useState(false)

  const { data: billingInfo, isLoading: billingLoading } = useQuery<BillingInfo>(
    'billing-info',
    async () => {
      const response = await api.get('/api/v1/billing/status')
      return response.data
    }
  )

  const handleUpgrade = async (plan: string) => {
    setIsLoading(true)
    try {
      const response = await api.post('/api/v1/billing/create-checkout-session', {
        plan_tier: plan,
        success_url: `${window.location.origin}/billing/success`,
        cancel_url: `${window.location.origin}/billing/cancel`
      })
      
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url
      } else {
        toast.error('Failed to create checkout session')
      }
    } catch (error) {
      toast.error('Failed to start upgrade process')
    } finally {
      setIsLoading(false)
    }
  }

  const handleManageBilling = async () => {
    try {
      const response = await api.post('/api/v1/billing/portal')
      if (response.data.portal_url) {
        window.open(response.data.portal_url, '_blank')
      } else {
        toast.error('Billing portal not available')
      }
    } catch (error) {
      toast.error('Failed to access billing portal')
    }
  }

  if (billingLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const currentPlan = plans[billingInfo?.plan || 'free']
  const usage = billingInfo?.usage || {
    queries_used: 0,
    queries_limit: currentPlan.limits.queries,
    documents_used: 0,
    documents_limit: currentPlan.limits.documents,
    storage_used: 0,
    storage_limit: currentPlan.limits.storage
  }

  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0 // unlimited
    return Math.min((used / limit) * 100, 100)
  }

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600 bg-red-100'
    if (percentage >= 75) return 'text-yellow-600 bg-yellow-100'
    return 'text-green-600 bg-green-100'
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Billing & Usage</h2>
        <p className="text-gray-500">Manage your subscription and view usage statistics</p>
      </div>

      {/* Current Plan */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Current Plan</h3>
            <p className="text-sm text-gray-500">
              {billingInfo?.status === 'active' ? 'Active' : 'Inactive'} • 
              {billingInfo?.cancel_at_period_end ? ' Cancels at period end' : ' Auto-renewal enabled'}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${
              billingInfo?.status === 'active' 
                ? 'text-green-600 bg-green-100' 
                : 'text-red-600 bg-red-100'
            }`}>
              {billingInfo?.status === 'active' ? 'Active' : 'Inactive'}
            </span>
            {billingInfo?.billing_portal_url && (
              <button
                onClick={handleManageBilling}
                className="btn btn-outline btn-sm"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Manage Billing
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{currentPlan.name}</div>
            <div className="text-sm text-gray-500">
              ${currentPlan.price}/month
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Next billing date</div>
            <div className="text-lg font-medium text-gray-900">
              {billingInfo?.current_period_end 
                ? new Date(billingInfo.current_period_end).toLocaleDateString()
                : 'N/A'
              }
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Plan features</div>
            <div className="text-lg font-medium text-gray-900">
              {currentPlan.features.length} features included
            </div>
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Usage This Month</h3>
        <div className="space-y-4">
          {/* Queries Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Queries</span>
              <span className="text-sm text-gray-500">
                {usage.queries_used.toLocaleString()} / {usage.queries_limit === -1 ? '∞' : usage.queries_limit.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  getUsagePercentage(usage.queries_used, usage.queries_limit) >= 90 ? 'bg-red-500' :
                  getUsagePercentage(usage.queries_used, usage.queries_limit) >= 75 ? 'bg-yellow-500' : 'bg-blue-500'
                }`}
                style={{ 
                  width: `${getUsagePercentage(usage.queries_used, usage.queries_limit)}%` 
                }}
              />
            </div>
          </div>

          {/* Documents Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Documents</span>
              <span className="text-sm text-gray-500">
                {usage.documents_used.toLocaleString()} / {usage.documents_limit === -1 ? '∞' : usage.documents_limit.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  getUsagePercentage(usage.documents_used, usage.documents_limit) >= 90 ? 'bg-red-500' :
                  getUsagePercentage(usage.documents_used, usage.documents_limit) >= 75 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ 
                  width: `${getUsagePercentage(usage.documents_used, usage.documents_limit)}%` 
                }}
              />
            </div>
          </div>

          {/* Storage Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Storage</span>
              <span className="text-sm text-gray-500">
                {(usage.storage_used / 1024 / 1024).toFixed(1)} MB / {usage.storage_limit === -1 ? '∞' : `${usage.storage_limit} MB`}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  getUsagePercentage(usage.storage_used, usage.storage_limit * 1024 * 1024) >= 90 ? 'bg-red-500' :
                  getUsagePercentage(usage.storage_used, usage.storage_limit * 1024 * 1024) >= 75 ? 'bg-yellow-500' : 'bg-purple-500'
                }`}
                style={{ 
                  width: `${getUsagePercentage(usage.storage_used, usage.storage_limit * 1024 * 1024)}%` 
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Available Plans */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(plans).map(([key, plan]) => (
            <div
              key={key}
              className={`relative rounded-lg border p-6 ${
                billingInfo?.plan === key
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200'
              }`}
            >
              {billingInfo?.plan === key && (
                <div className="absolute top-4 right-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Current Plan
                  </span>
                </div>
              )}
              
              <div className="text-center">
                <h4 className="text-lg font-medium text-gray-900">{plan.name}</h4>
                <div className="mt-2">
                  <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                  <span className="text-gray-500">/month</span>
                </div>
              </div>

              <ul className="mt-6 space-y-3">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-6">
                {billingInfo?.plan === key ? (
                  <button
                    disabled
                    className="w-full btn btn-outline"
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(key)}
                    disabled={isLoading}
                    className="w-full btn btn-primary"
                  >
                    {isLoading ? 'Processing...' : `Upgrade to ${plan.name}`}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Billing History */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Billing History</h3>
        <div className="text-center py-8">
          <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No billing history</h3>
          <p className="mt-1 text-sm text-gray-500">
            Your billing history will appear here once you have active subscriptions.
          </p>
        </div>
      </div>
    </div>
  )
}
