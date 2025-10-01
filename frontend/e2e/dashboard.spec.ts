import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token');
    });

    // Mock API responses
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1',
          username: 'demo',
          email: 'demo@example.com',
          full_name: 'Demo User',
          email_verified: true
        })
      });
    });

    await page.route('**/api/analytics/overview', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_messages: 150,
          active_sessions: 5,
          avg_response_time: 1200,
          top_questions: [
            { question: 'How do I reset my password?', count: 25 },
            { question: 'What are your business hours?', count: 20 }
          ]
        })
      });
    });

    await page.route('**/api/analytics/usage-stats**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { date: '2024-01-01', messages_count: 10 },
          { date: '2024-01-02', messages_count: 15 },
          { date: '2024-01-03', messages_count: 12 }
        ])
      });
    });

    await page.route('**/api/analytics/kpis**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          queries: { delta_pct: 15.5 },
          sessions: { delta_pct: 8.2 },
          avg_response_time_ms: { delta_ms: -200 },
          active_sessions: { delta: 2 }
        })
      });
    });

    await page.route('**/api/billing/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          plan: 'starter',
          status: 'active',
          is_trial: false,
          usage: {
            queries_used: 150,
            queries_limit: 1000
          }
        })
      });
    });
  });

  test('should load dashboard overview', async ({ page }) => {
    await page.goto('/dashboard');

    // Check if dashboard loads
    await expect(page.getByRole('heading', { name: /Dashboard Overview/i })).toBeVisible();

    // Check if stats cards are present
    await expect(page.getByText('Total Queries')).toBeVisible();
    await expect(page.getByText('This Month')).toBeVisible();
    await expect(page.getByText('Active Users')).toBeVisible();
    await expect(page.getByText('Avg Response Time')).toBeVisible();

    // Check if charts are present
    await expect(page.getByText('Query Volume')).toBeVisible();
    await expect(page.getByText('Top Questions This Month')).toBeVisible();
  });

  test('should navigate between dashboard sections', async ({ page }) => {
    await page.goto('/dashboard');

    // Navigate to Documents
    await page.getByRole('link', { name: 'Documents' }).click();
    await expect(page).toHaveURL('/dashboard/documents');
    await expect(page.getByRole('heading', { name: /Document Manager/i })).toBeVisible();

    // Navigate to Embed Widget
    await page.getByRole('link', { name: 'Embed Widget' }).click();
    await expect(page).toHaveURL('/dashboard/embed');
    await expect(page.getByRole('heading', { name: /Embed Widget/i })).toBeVisible();

    // Navigate to Analytics
    await page.getByRole('link', { name: 'Analytics' }).click();
    await expect(page).toHaveURL('/dashboard/analytics');
    await expect(page.getByRole('heading', { name: /Analytics/i })).toBeVisible();

    // Navigate to Settings
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/dashboard/settings');
    await expect(page.getByRole('heading', { name: /Settings/i })).toBeVisible();
  });

  test('should display user menu', async ({ page }) => {
    await page.goto('/dashboard');

    // Click on user menu
    await page.getByText('Demo User').click();

    // Check if dropdown menu is visible
    await expect(page.getByText('Settings')).toBeVisible();
    await expect(page.getByText('Sign out')).toBeVisible();
  });

  test('should handle logout', async ({ page }) => {
    await page.goto('/dashboard');

    // Click on user menu
    await page.getByText('Demo User').click();
    
    // Click logout
    await page.getByText('Sign out').click();

    // Should redirect to home page
    await expect(page).toHaveURL('/');
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // Check if mobile menu button is visible
    await expect(page.getByRole('button', { name: /menu/i })).toBeVisible();
    
    // Click mobile menu
    await page.getByRole('button', { name: /menu/i }).click();
    
    // Check if sidebar is visible
    await expect(page.getByText('Documents')).toBeVisible();
    await expect(page.getByText('Embed Widget')).toBeVisible();
  });

  test('should refresh data when refresh button is clicked', async ({ page }) => {
    await page.goto('/dashboard');

    // Click refresh button
    await page.getByRole('button', { name: /Refresh/i }).click();

    // Should show loading state briefly
    await expect(page.getByRole('button', { name: /Refresh/i })).toBeDisabled();
  });
});
