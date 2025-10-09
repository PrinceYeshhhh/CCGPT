import { test, expect } from '@playwright/test'

test.describe('Auth to Dashboard Journey', () => {
  test('redirects to login, logs in, and navigates dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/.*login/)

    // If login form present, fill it, otherwise skip (environment dependent)
    const email = page.locator('input[type="email"]')
    const password = page.locator('input[type="password"]')
    if (await email.count()) {
      await email.fill('test@example.com')
      await password.fill('Password123!')
      await page.getByRole('button', { name: /log in/i }).click()
    }

    // Land on dashboard
    await expect(page).toHaveURL(/.*dashboard/)

    // Navigate to Documents and Analytics
    await page.getByRole('link', { name: /documents/i }).click()
    await expect(page).toHaveURL(/.*dashboard\/documents/)

    await page.getByRole('link', { name: /analytics/i }).click()
    await expect(page).toHaveURL(/.*dashboard\/analytics/)
  })
})


