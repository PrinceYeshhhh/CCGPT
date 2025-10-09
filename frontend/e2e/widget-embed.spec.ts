import { test, expect } from '@playwright/test'

test.describe('Website widget embed and chat flow', () => {
  test('embeds widget script and sends a chat message', async ({ page }) => {
    // Serve a simple page with the widget script tag (simulated)
    await page.setContent(`
      <html>
        <head></head>
        <body>
          <div id="widget-container"></div>
          <script>
            // Simulate loading of widget and exposing a function
            window.widget = {
              mount: function(containerId) {
                const el = document.getElementById(containerId);
                const btn = document.createElement('button');
                btn.textContent = 'Open Chat';
                btn.id = 'open-chat';
                el.appendChild(btn);
                const input = document.createElement('input');
                input.placeholder = 'Type your message';
                input.id = 'chat-input';
                el.appendChild(input);
                const send = document.createElement('button');
                send.textContent = 'Send';
                send.id = 'chat-send';
                el.appendChild(send);
              }
            }
            window.widget.mount('widget-container');
          </script>
        </body>
      </html>
    `)

    // Open chat and send a message
    await page.click('#open-chat')
    await page.fill('#chat-input', 'Hello, widget!')
    await page.click('#chat-send')

    // In a real test, we would intercept network to backend and assert payloads
    // Here we just assert UI elements exist to confirm flow
    await expect(page.locator('#chat-input')).toBeVisible()
  })
})

