import { Page, expect } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Mock authentication for tests
   */
  async mockAuth(user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
    email_verified?: boolean;
  }) {
    await this.page.addInitScript((user) => {
      localStorage.setItem('auth_token', 'mock-token');
      localStorage.setItem('user', JSON.stringify(user));
    }, user);

    await this.page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(user)
      });
    });
  }

  /**
   * Mock API response
   */
  async mockApiResponse(url: string, response: any, status = 200) {
    await this.page.route(`**${url}`, async route => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoading() {
    await this.page.waitForLoadState('networkidle');
    // Wait for any loading spinners to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('[data-testid="loading"], .animate-spin');
      return spinners.length === 0;
    }, { timeout: 10000 });
  }

  /**
   * Take screenshot for debugging
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  /**
   * Check if element is visible and clickable
   */
  async expectElementToBeClickable(selector: string) {
    const element = this.page.locator(selector);
    await expect(element).toBeVisible();
    await expect(element).toBeEnabled();
  }

  /**
   * Fill form field with validation
   */
  async fillFormField(label: string, value: string) {
    const field = this.page.getByLabel(label);
    await field.clear();
    await field.fill(value);
    await expect(field).toHaveValue(value);
  }

  /**
   * Submit form and wait for response
   */
  async submitForm(buttonText: string) {
    const submitButton = this.page.getByRole('button', { name: buttonText });
    await submitButton.click();
    await this.waitForLoading();
  }

  /**
   * Check for toast notifications
   */
  async expectToast(message: string, type: 'success' | 'error' | 'info' = 'success') {
    const toast = this.page.locator(`[data-testid="toast-${type}"]`);
    await expect(toast).toBeVisible();
    await expect(toast).toContainText(message);
  }

  /**
   * Mock file upload
   */
  async mockFileUpload(fileName: string, fileContent: string) {
    await this.page.route('**/api/documents/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          document_id: 'mock-id',
          job_id: 'mock-job-id',
          message: 'File uploaded successfully'
        })
      });
    });
  }

  /**
   * Check responsive design
   */
  async checkResponsive(viewport: { width: number; height: number }) {
    await this.page.setViewportSize(viewport);
    await this.page.reload();
    await this.waitForLoading();
  }

  /**
   * Wait for API call to complete
   */
  async waitForApiCall(url: string) {
    await this.page.waitForResponse(response => 
      response.url().includes(url) && response.status() === 200
    );
  }

  /**
   * Mock error response
   */
  async mockApiError(url: string, error: { detail: string; message?: string }, status = 400) {
    await this.page.route(`**${url}`, async route => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(error)
      });
    });
  }
}
