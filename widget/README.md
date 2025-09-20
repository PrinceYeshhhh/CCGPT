# CustomerCareGPT Widget

The embeddable chat widget for CustomerCareGPT.

## Usage

### Basic Integration

Add this script to your website before the closing `</body>` tag:

```html
<script>
  window.CustomerCareGPTConfig = {
    codeId: 'your-embed-code-id',
    title: 'Customer Support',
    primaryColor: '#007bff',
    position: 'bottom-right'
  };
</script>
<script src="https://your-domain.com/widget/widget.js"></script>
```

### Advanced Configuration

```html
<script>
  window.CustomerCareGPTConfig = {
    codeId: 'your-embed-code-id',
    title: 'Customer Support',
    placeholder: 'Ask me anything...',
    primaryColor: '#007bff',
    position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
    showAvatar: true,
    avatarUrl: 'https://example.com/avatar.png',
    welcomeMessage: 'Hello! How can I help you today?',
    maxMessages: 50,
    enableSound: true,
    enableTypingIndicator: true
  };
</script>
<script src="https://your-domain.com/widget/widget.js"></script>
```

### Programmatic Control

```javascript
// Open the chat widget
CustomerCareGPT.open();

// Close the chat widget
CustomerCareGPT.close();

// Send a message programmatically
CustomerCareGPT.sendMessage('Hello, I need help with my order');
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `codeId` | string | null | Your embed code ID (required) |
| `title` | string | 'Customer Support' | Widget title |
| `placeholder` | string | 'Ask me anything...' | Input placeholder text |
| `primaryColor` | string | '#007bff' | Primary color for the widget |
| `position` | string | 'bottom-right' | Widget position on screen |
| `showAvatar` | boolean | true | Show avatar in header |
| `avatarUrl` | string | '' | Custom avatar URL |
| `welcomeMessage` | string | 'Hello! How can I help you today?' | Initial message |
| `maxMessages` | number | 50 | Maximum messages to keep in chat |
| `enableSound` | boolean | true | Enable notification sounds |
| `enableTypingIndicator` | boolean | true | Show typing indicator |

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## License

Proprietary - All rights reserved
