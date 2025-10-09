import { test, expect, devices } from '@playwright/test'

test.use({ ...devices['Pixel 5'] })

test.describe('Mobile journeys', () => {
  test('Home renders and opens mobile nav', async ({ page }) => {
    await page.goto('/')
    const menu = page.getByRole('button', { name: /menu|open navigation/i })
    if (await menu.count()) {
      await menu.click()
      await expect(page.getByRole('navigation')).toBeVisible()
    }
  })

  test('Dashboard landing renders on mobile after login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/login/)
    // Attempt login if form present
    const email = page.locator('input[type="email"]')
    const password = page.locator('input[type="password"]')
    if (await email.count()) {
      await email.fill('test@example.com')
      await password.fill('Password123!')
      await page.getByRole('button', { name: /log in/i }).click()
      await expect(page).toHaveURL(/dashboard/)
    }
  })
})


