import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Check, Star } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'

export function Pricing() {
  const { isAuthenticated } = useAuth() as any

  const plans = [
    { name: 'Starter', price: 29, description: 'Perfect for small businesses getting started', popular: false, features: ['1,000 queries/month','Up to 5 documents','Basic customization','Email support','Analytics dashboard','Embed widget'], planTier: 'starter' },
    { name: 'Pro', price: 79, description: 'Ideal for growing businesses', popular: true, features: ['10,000 queries/month','Up to 50 documents','Advanced customization','Priority support','Advanced analytics','Custom branding','API access','Webhooks'], planTier: 'pro' },
    { name: 'Enterprise', price: 299, description: 'For large organizations with custom needs', popular: false, features: ['Unlimited queries','Unlimited documents','White-label solution','Dedicated support','Custom integrations','SSO/SAML','SLA guarantee','Custom training'], planTier: 'enterprise' },
  ]

  const handleSubscribe = async (plan_tier: string) => {
    if (!isAuthenticated) {
      window.location.href = '/login'
      return
    }
    try {
      const res = await api.post('/api/v1/billing/create-checkout-session', {
        plan_tier,
        success_url: `${window.location.origin}/dashboard/billing`,
        cancel_url: `${window.location.origin}/pricing`
      })
      if (res.data?.checkout_url) {
        window.location.href = res.data.checkout_url
      }
    } catch (e) {
      // noop
    }
  }

  return (
    <div className="min-h-screen bg-background py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6">Simple, Transparent Pricing</h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">Choose the plan that fits your business needs. All plans include a 14-day free trial.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <Card key={plan.name} className={`relative ${plan.popular ? 'border-blue-500 ring-2 ring-blue-500/20' : ''}`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center">
                    <Star className="h-4 w-4 mr-1" /> Most Popular
                  </div>
                </div>
              )}
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                <div className="mt-4">
                  <span className="text-4xl font-bold">${plan.price}</span>
                  <span className="text-muted-foreground">/month</span>
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
                <Button className="w-full" variant={plan.popular ? 'primary' : 'outline'} onClick={() => handleSubscribe(plan.planTier)}>
                  {isAuthenticated ? 'Start Free Trial' : 'Sign in to Subscribe'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
