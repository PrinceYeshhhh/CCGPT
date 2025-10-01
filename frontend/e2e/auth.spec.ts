import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/login');

    // Check if login form elements are present
    await expect(page.getByRole('heading', { name: /Sign in to your account/i })).toBeVisible();
    await expect(page.getByLabel(/Username or Email/i)).toBeVisible();
    await expect(page.getByLabel(/Password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Login/i })).toBeVisible();

    // Check if demo credentials are shown
    await expect(page.getByText(/Demo credentials/i)).toBeVisible();
    await expect(page.getByText(/Username: demo/i)).toBeVisible();
    await expect(page.getByText(/Password: demo123/i)).toBeVisible();
  });

  test('should display register form', async ({ page }) => {
    await page.goto('/register');

    // Check if register form elements are present
    await expect(page.getByRole('heading', { name: /Create your account/i })).toBeVisible();
    await expect(page.getByLabel(/Full Name/i)).toBeVisible();
    await expect(page.getByLabel(/Email/i)).toBeVisible();
    await expect(page.getByLabel(/Password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Create Account/i })).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/login');
    
    // Try to submit empty form
    await page.getByRole('button', { name: /Login/i }).click();
    
    // Check for validation errors
    await expect(page.getByText(/Username or email is required/i)).toBeVisible();
    await expect(page.getByText(/Password must be at least 6 characters/i)).toBeVisible();
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in invalid email
    await page.getByLabel(/Username or Email/i).fill('invalid-email');
    await page.getByLabel(/Password/i).fill('password123');
    await page.getByRole('button', { name: /Login/i }).click();
    
    // Check for validation error
    await expect(page.getByText(/Invalid email format/i)).toBeVisible();
  });

  test('should show validation error for short password', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in short password
    await page.getByLabel(/Username or Email/i).fill('test@example.com');
    await page.getByLabel(/Password/i).fill('123');
    await page.getByRole('button', { name: /Login/i }).click();
    
    // Check for validation error
    await expect(page.getByText(/Password must be at least 6 characters/i)).toBeVisible();
  });

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login');
    
    // Click on sign up link
    await page.getByText(/Don't have an account/i).click();
    await expect(page).toHaveURL('/register');
    
    // Click on sign in link
    await page.getByText(/Already have an account/i).click();
    await expect(page).toHaveURL('/login');
  });

  test('should handle demo login', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in demo credentials
    await page.getByLabel(/Username or Email/i).fill('demo');
    await page.getByLabel(/Password/i).fill('demo123');
    
    // Mock successful login response
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          user: {
            id: '1',
            username: 'demo',
            email: 'demo@example.com',
            full_name: 'Demo User'
          }
        })
      });
    });
    
    await page.getByRole('button', { name: /Login/i }).click();
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('should handle login error', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in invalid credentials
    await page.getByLabel(/Username or Email/i).fill('test@example.com');
    await page.getByLabel(/Password/i).fill('wrongpassword');
    
    // Mock error response
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid credentials'
        })
      });
    });
    
    await page.getByRole('button', { name: /Login/i }).click();
    
    // Should show error message
    await expect(page.getByText(/Invalid credentials/i)).toBeVisible();
  });
});
