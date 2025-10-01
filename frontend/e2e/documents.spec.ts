import { test, expect } from '@playwright/test';

test.describe('Document Management', () => {
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
          full_name: 'Demo User'
        })
      });
    });

    await page.route('**/api/documents/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            name: 'FAQ.pdf',
            status: 'active',
            created_at: '2024-01-01T00:00:00Z',
            size: 1024000
          },
          {
            id: '2',
            name: 'User Guide.docx',
            status: 'processing',
            created_at: '2024-01-02T00:00:00Z',
            size: 2048000
          }
        ])
      });
    });
  });

  test('should display document list', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Check if page loads
    await expect(page.getByRole('heading', { name: /Document Manager/i })).toBeVisible();

    // Check if documents are displayed
    await expect(page.getByText('FAQ.pdf')).toBeVisible();
    await expect(page.getByText('User Guide.docx')).toBeVisible();

    // Check if status indicators are present
    await expect(page.getByText('Active')).toBeVisible();
    await expect(page.getByText('Processing...')).toBeVisible();
  });

  test('should show upload area', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Check if upload area is present
    await expect(page.getByText(/Drag & drop files here/i)).toBeVisible();
    await expect(page.getByText(/Supports PDF, DOC, DOCX, TXT, MD files/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Select Files/i })).toBeVisible();
  });

  test('should handle file upload', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Mock successful upload response
    await page.route('**/api/documents/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          document_id: '3',
          job_id: 'job_123',
          message: 'File uploaded successfully'
        })
      });
    });

    // Create a test file
    const filePath = 'test-document.pdf';
    await page.setInputFiles('input[type="file"]', filePath);

    // Check if file appears in the list
    await expect(page.getByText('test-document.pdf')).toBeVisible();
  });

  test('should handle document deletion', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Mock successful deletion response
    await page.route('**/api/documents/1', async route => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Document deleted successfully' })
        });
      }
    });

    // Click delete button for first document
    await page.locator('[data-testid="delete-document-1"]').click();

    // Check if document is removed from list
    await expect(page.getByText('FAQ.pdf')).not.toBeVisible();
  });

  test('should handle document reprocessing', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Mock successful reprocessing response
    await page.route('**/api/documents/1/reprocess', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job_456',
          message: 'Document queued for reprocessing'
        })
      });
    });

    // Click reprocess button for first document
    await page.locator('[data-testid="reprocess-document-1"]').click();

    // Check if status changes to processing
    await expect(page.getByText('Processing...')).toBeVisible();
  });

  test('should show document selection for query', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Select a document
    await page.locator('input[type="checkbox"]').first().check();

    // Check if query section is enabled
    await expect(page.getByText(/Ask about Selected Documents/i)).toBeVisible();
    await expect(page.getByPlaceholder(/Type your question/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Ask/i })).toBeEnabled();
  });

  test('should handle document query', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Mock query response
    await page.route('**/api/production_rag/query', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: 'This is a sample answer based on the selected documents.',
          sources: ['FAQ.pdf']
        })
      });
    });

    // Select a document
    await page.locator('input[type="checkbox"]').first().check();

    // Type a question
    await page.getByPlaceholder(/Type your question/i).fill('How do I reset my password?');
    
    // Click ask button
    await page.getByRole('button', { name: /Ask/i }).click();

    // Check if answer is displayed
    await expect(page.getByText(/This is a sample answer/i)).toBeVisible();
  });

  test('should show processing status with progress bar', async ({ page }) => {
    await page.goto('/dashboard/documents');

    // Check if processing document shows progress bar
    const processingDocument = page.locator('text=User Guide.docx').locator('..');
    await expect(processingDocument.locator('[role="progressbar"]')).toBeVisible();
    await expect(processingDocument.locator('text=Processing content...')).toBeVisible();
  });
});
