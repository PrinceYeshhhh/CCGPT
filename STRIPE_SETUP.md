# Stripe Billing Setup Guide

This guide explains how to configure Stripe billing for CustomerCareGPT, including webhook setup, price configuration, and testing.

## Prerequisites

1. Stripe account (test mode for development)
2. Stripe CLI installed locally
3. CustomerCareGPT backend running

## 1. Stripe Dashboard Configuration

### Create Products and Prices

1. **Starter Plan**
   - Product Name: "CustomerCareGPT Starter"
   - Price: $29/month
   - Billing: Recurring monthly
   - Copy the Price ID (e.g., `price_1234567890`)

2. **Pro Plan**
   - Product Name: "CustomerCareGPT Pro"
   - Price: $99/month
   - Billing: Recurring monthly
   - Copy the Price ID (e.g., `price_0987654321`)

3. **Enterprise Plan**
   - Product Name: "CustomerCareGPT Enterprise"
   - Price: $299/month
   - Billing: Recurring monthly
   - Copy the Price ID (e.g., `price_1122334455`)

4. **White-Label Plan**
   - Product Name: "CustomerCareGPT White-Label"
   - Price: $999 (one-time)
   - Billing: One-time payment
   - Copy the Price ID (e.g., `price_5566778899`)

### Configure Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://your-backend.com/api/v1/billing/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the webhook signing secret (starts with `whsec_`)

## 2. Environment Configuration

Update your `.env` file with Stripe credentials:

```bash
# Stripe Configuration
STRIPE_API_KEY=sk_test_your_test_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_SUCCESS_URL=https://your-frontend.com/billing/success
STRIPE_CANCEL_URL=https://your-frontend.com/billing/cancel
BILLING_DEFAULT_TIER=starter

# Stripe Price IDs (from Dashboard)
STRIPE_STARTER_PRICE_ID=price_1234567890
STRIPE_PRO_PRICE_ID=price_0987654321
STRIPE_ENTERPRISE_PRICE_ID=price_1122334455
STRIPE_WHITE_LABEL_PRICE_ID=price_5566778899
```

## 3. Database Migration

Run the Alembic migration to create the subscriptions table:

```bash
cd backend
alembic upgrade head
```

## 4. Local Webhook Testing

### Using Stripe CLI

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login to your Stripe account:
   ```bash
   stripe login
   ```
3. Forward webhooks to your local server:
   ```bash
   stripe listen --forward-to https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/billing/webhook
   ```
4. Copy the webhook signing secret from the CLI output
5. Update your `.env` file with the CLI webhook secret

### Test Webhook Events

1. Trigger test events:
   ```bash
   stripe trigger checkout.session.completed
   stripe trigger invoice.payment_succeeded
   stripe trigger customer.subscription.updated
   ```

2. Check your application logs to verify webhook processing

## 5. Testing the Billing Flow

### Test Checkout Session Creation

```bash
curl -X POST "https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/billing/create-checkout-session" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_tier": "starter",
    "success_url": "https://your-frontend.com/billing/success",
    "cancel_url": "https://your-frontend.com/billing/cancel"
  }'
```

### Test Quota Enforcement

1. Create a test subscription with limited quota
2. Make API calls to `/api/v1/rag/query`
3. Verify quota is enforced when limit is reached

### Test White-Label Purchase

```bash
curl -X POST "https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/white-label/purchase" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_tier": "white_label",
    "success_url": "https://your-frontend.com/billing/white-label/success",
    "cancel_url": "https://your-frontend.com/billing/white-label/cancel"
  }'
```

## 6. Production Deployment

### Webhook Endpoint Security

1. Use HTTPS for webhook endpoints
2. Verify webhook signatures in production
3. Implement idempotency for webhook handlers
4. Log all webhook events for debugging

### Environment Variables

Update production environment with live Stripe keys:

```bash
STRIPE_API_KEY=sk_live_your_live_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_production_webhook_secret
```

### Database Considerations

1. Ensure proper indexing on subscription queries
2. Consider Redis for high-volume quota tracking
3. Implement database connection pooling
4. Set up monitoring for subscription events

## 7. Monitoring and Analytics

### Key Metrics to Track

1. **Conversion Rates**
   - Checkout session completion rate
   - Plan upgrade rates
   - Churn rates by plan

2. **Usage Patterns**
   - Queries per workspace
   - Peak usage times
   - Quota utilization

3. **Revenue Metrics**
   - Monthly recurring revenue (MRR)
   - Customer lifetime value (CLV)
   - Average revenue per user (ARPU)

### Stripe Dashboard Monitoring

1. Monitor failed payments
2. Track subscription changes
3. Review webhook delivery success rates
4. Set up alerts for critical events

## 8. Troubleshooting

### Common Issues

1. **Webhook Signature Verification Failed**
   - Check webhook secret configuration
   - Ensure raw request body is used for verification

2. **Quota Not Enforced**
   - Verify subscription status in database
   - Check quota middleware is applied to endpoints
   - Review usage increment logic

3. **Checkout Session Creation Failed**
   - Verify Stripe API key is correct
   - Check price IDs are valid
   - Ensure customer creation succeeds

### Debug Commands

```bash
# Check subscription status
curl -H "Authorization: Bearer TOKEN" \
  https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/billing/status

# Get quota information
curl -H "Authorization: Bearer TOKEN" \
  https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/billing/quota

# Test webhook endpoint
curl -X POST https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/billing/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

## 9. Security Best Practices

1. **Never store raw card data** - Use Stripe Checkout or Elements
2. **Verify webhook signatures** - Always validate webhook authenticity
3. **Use HTTPS** - Encrypt all communication
4. **Implement rate limiting** - Protect against abuse
5. **Log security events** - Monitor for suspicious activity
6. **Regular security audits** - Review code and configurations

## 10. Support and Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [CustomerCareGPT Support](mailto:support@customercaregpt.com)

## Plan Definitions

| Plan | Monthly Price | Queries | Documents | Features |
|------|---------------|---------|-----------|----------|
| Free | $0 | 100 | 5 | Basic support |
| Starter | $29 | 5,000 | 5 | Email support |
| Pro | $99 | 100,000 | Unlimited | Priority support, API access |
| Enterprise | $299 | Unlimited | Unlimited | 24/7 support, custom integrations |
| White-Label | $999 (one-time) | Unlimited | Unlimited | Full white-label solution |

## Next Steps

1. Set up Stripe test environment
2. Configure webhooks
3. Test billing flow end-to-end
4. Deploy to production
5. Monitor and optimize

For additional support, contact the development team or refer to the Stripe documentation.
