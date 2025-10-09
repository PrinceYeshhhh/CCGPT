import { test, expect } from '@playwright/test'

test.describe('Accessibility and Screenshots', () => {
  const routes = ['/', '/features', '/pricing', '/faq', '/dashboard']

  for (const route of routes) {
    test(`route ${route} loads and matches baseline screenshot`, async ({ page }) => {
      await page.goto(route)
      await expect(page).toHaveURL(new RegExp(route === '/' ? '\\/$' : route))
      await expect(page).toHaveScreenshot({ fullPage: true })
    })
  }
})


