import { test, expect } from '@playwright/test';

// E2E test to verify rotating greeting messages in the embedded widget.
// We mock the widget script endpoint and serve a minimal script that includes
// the same rotation logic implemented in the backend-generated script.

test.describe('Embedded widget rotating greetings', () => {
  test('rotates greeting message on each open', async ({ page }) => {
    await page.route('**/api/v1/embed/widget/**', async (route) => {
      const js = `
        (function() {
          const CONFIG = {
            embedCodeId: 'mock',
            welcomeMessage: 'Fallback hello',
            welcomeMessages: [
              'Hi there 👋, I’m your virtual customer care assistant. How can I help you today?',
              'Hello! I’m here to help with orders, billing, and more — what do you need?',
              'Welcome! Need help tracking an order or managing your account? Ask away.'
            ]
          };

          let isOpen = false;

          function getGreetingIndexKey() {
            return \'ccgpt_greet_idx_\' + CONFIG.embedCodeId;
          }

          function getWelcomeMessage() {
            const arr = Array.isArray(CONFIG.welcomeMessages) ? CONFIG.welcomeMessages : [];
            if (arr.length === 0) return CONFIG.welcomeMessage || '';
            let idx = 0;
            try {
              const stored = localStorage.getItem(getGreetingIndexKey());
              idx = stored ? parseInt(stored, 10) || 0 : 0;
            } catch (e) { idx = 0; }
            const msg = arr[idx % arr.length] || CONFIG.welcomeMessage || '';
            try { localStorage.setItem(getGreetingIndexKey(), String((idx + 1) % arr.length)); } catch (e) {}
            return msg;
          }

          function addMessage(content, type) {
            const messagesContainer = document.getElementById('ccgpt-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'ccgpt-message ccgpt-' + type;
            messageDiv.textContent = content;
            messagesContainer.appendChild(messageDiv);
          }

          function toggleChat() {
            isOpen = !isOpen;
            const chatContainer = document.getElementById('ccgpt-chat-container');
            chatContainer.style.display = isOpen ? 'block' : 'none';
            if (isOpen) {
              const greet = getWelcomeMessage();
              if (greet) addMessage(greet, 'bot');
            }
          }

          // Initialize minimal DOM for widget
          const root = document.createElement('div');
          root.innerHTML = `
            <div id="ccgpt-chat-container" style="display:none"></div>
            <div id="ccgpt-messages"></div>
            <button id="ccgpt-toggle">open</button>
          `;
          document.body.appendChild(root);
          document.getElementById('ccgpt-toggle').addEventListener('click', toggleChat);
        })();
      `;
      await route.fulfill({ status: 200, contentType: 'application/javascript', body: js });
    });

    // Start from a clean localStorage state
    await page.goto('about:blank');
    await page.evaluate(() => localStorage.clear());

    // Inject the mocked widget script
    await page.setContent('<html><body></body></html>');
    await page.addScriptTag({ url: 'http://localhost/api/v1/embed/widget/mock' });

    const toggle = page.locator('#ccgpt-toggle');
    const messages = page.locator('.ccgpt-message.ccgpt-bot');

    // Open/close/open/close/open to trigger three greetings in sequence
    await toggle.click(); // open -> greet[0]
    await expect(messages.nth(0)).toContainText('virtual customer care assistant');

    await toggle.click(); // close
    await toggle.click(); // open -> greet[1]
    await expect(messages.nth(1)).toContainText('orders, billing, and more');

    await toggle.click(); // close
    await toggle.click(); // open -> greet[2]
    await expect(messages.nth(2)).toContainText('tracking an order');

    // Verify rotation persisted in localStorage (next should wrap to index 0)
    await toggle.click(); // close
    await toggle.click(); // open -> greet[0] again
    await expect(messages.nth(3)).toContainText('virtual customer care assistant');
  });
});


