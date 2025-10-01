import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load homepage and display main elements', async ({ page }) => {
    await page.goto('/');

    // Check if the main heading is visible
    await expect(page.getByRole('heading', { name: /AI Customer Support That Actually Works/i })).toBeVisible();

    // Check if navigation is present
    await expect(page.getByRole('navigation')).toBeVisible();
    await expect(page.getByText('CustomerCareGPT')).toBeVisible();

    // Check if main navigation links are present
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Features' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Pricing' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'FAQ' })).toBeVisible();

    // Check if CTA buttons are present
    await expect(page.getByRole('button', { name: /Start Free Trial/i })).toBeVisible();
    await expect(page.getByRole('link', { name: 'View Pricing' })).toBeVisible();
  });

  test('should navigate to features page', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('link', { name: 'Features' }).click();
    await expect(page).toHaveURL('/features');
    await expect(page.getByRole('heading', { name: /Features/i })).toBeVisible();
  });

  test('should navigate to pricing page', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('link', { name: 'Pricing' }).click();
    await expect(page).toHaveURL('/pricing');
    await expect(page.getByRole('heading', { name: /Pricing/i })).toBeVisible();
  });

  test('should navigate to FAQ page', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('link', { name: 'FAQ' }).click();
    await expect(page).toHaveURL('/faq');
    await expect(page.getByRole('heading', { name: /FAQ/i })).toBeVisible();
  });

  test('should have working theme toggle', async ({ page }) => {
    await page.goto('/');
    
    const themeToggle = page.getByRole('button', { name: /theme/i });
    await expect(themeToggle).toBeVisible();
    
    // Click theme toggle and check if theme changes
    await themeToggle.click();
    
    // Check if dark mode is applied (this depends on your implementation)
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check if mobile menu button is visible
    await expect(page.getByRole('button', { name: /menu/i })).toBeVisible();
    
    // Check if main content is still visible
    await expect(page.getByRole('heading', { name: /AI Customer Support That Actually Works/i })).toBeVisible();
  });
});
