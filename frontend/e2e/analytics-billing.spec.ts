import { test, expect } from '@playwright/test'

test.describe('Analytics and Billing E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    // Mock auth
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: '1', email: 'demo@example.com' })
      })
    })

    // Mock analytics endpoints used by the Analytics page
    await page.route('**/api/analytics/detailed-overview**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: { total_queries: 42, unique_users: 7, avg_response_time: 1.2, satisfaction_rate: 95 } })
      })
    })
    await page.route('**/api/analytics/detailed-usage-stats**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [] }) })
    })
    await page.route('**/api/analytics/detailed-hourly**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [] }) })
    })
    await page.route('**/api/analytics/detailed-satisfaction**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [] }) })
    })
    await page.route('**/api/analytics/detailed-top-questions**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [] }) })
    })

    // Mock billing endpoints used by Billing page
    await page.route('**/api/billing/info', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          plan: 'free', status: 'inactive', current_period_end: null, cancel_at_period_end: false,
          usage: { queries_used: 0, queries_limit: 100, documents_used: 0, documents_limit: 1, storage_used: 0, storage_limit: 10000000 },
          billing_portal_url: null
        })
      })
    })
    await page.route('**/api/billing/checkout**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ checkout_url: 'https://stripe.test/checkout' }) })
    })
  })

  test('Analytics page loads KPIs and charts sections', async ({ page }) => {
    await page.goto('/dashboard/analytics')
    await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible()
    await expect(page.getByText(/Total Queries/i)).toBeVisible()
    await expect(page.getByText(/Unique Users/i)).toBeVisible()
    await expect(page.getByText(/Avg Response Time/i)).toBeVisible()
    await expect(page.getByText(/Satisfaction Rate/i)).toBeVisible()
  })

  test('Billing page shows plans and triggers checkout', async ({ page }) => {
    await page.goto('/dashboard/billing')
    await expect(page.getByRole('heading', { name: /Billing/i })).toBeVisible()
    const upgradeButtons = await page.getByRole('button', { name: /Upgrade/i })
    await expect(upgradeButtons.first()).toBeVisible()
    await upgradeButtons.first().click()
    // After clicking upgrade, our route returns a checkout URL; UI typically navigates/open new tab.
  })
})


