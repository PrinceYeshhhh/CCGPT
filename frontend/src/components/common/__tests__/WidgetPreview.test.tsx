import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WidgetPreview } from '../WidgetPreview';

const mockConfig = {
  title: 'Customer Support',
  welcome_message: 'Hi! How can I help you today?',
  placeholder: 'Ask me anything...',
  primary_color: '#3b82f6',
  secondary_color: '#f8f9fa',
  text_color: '#111111',
  position: 'bottom-right',
  show_avatar: true,
  avatar_url: 'https://example.com/avatar.jpg',
  enable_sound: true,
  enable_typing_indicator: true,
  enable_websocket: true,
  theme: 'light',
  custom_css: '.custom { color: red; }',
  max_messages: 50,
};

describe('WidgetPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWidgetPreview = (props = {}) => {
    const defaultProps = {
      isOpen: true,
      onClose: vi.fn(),
      config: mockConfig,
      ...props,
    };

    return render(<WidgetPreview {...defaultProps} />);
  };

  it('should render widget preview when open', () => {
    renderWidgetPreview();
    
    expect(screen.getByText('Widget Preview')).toBeInTheDocument();
    expect(screen.getByText('Customer Support')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    renderWidgetPreview({ isOpen: false });
    
    expect(screen.queryByText('Widget Preview')).not.toBeInTheDocument();
  });

  it('should display welcome message', () => {
    renderWidgetPreview();
    
    expect(screen.getByText('Hi! How can I help you today?')).toBeInTheDocument();
  });

  it('should display chat input', () => {
    renderWidgetPreview();
    
    expect(screen.getByPlaceholderText('Ask me anything...')).toBeInTheDocument();
  });

  it('should handle message sending', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('should handle enter key to send message', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('should not send empty message', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: '   ' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    expect(screen.queryByText('   ')).not.toBeInTheDocument();
  });

  it('should clear input after sending message', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    expect(input).toHaveValue('');
  });

  it('should display bot response', async () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Thank you for your message!')).toBeInTheDocument();
    });
  });

  it('should show typing indicator', async () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);
    
    expect(screen.getByText('Bot is typing...')).toBeInTheDocument();
  });

  it('should handle close button', () => {
    const onClose = vi.fn();
    renderWidgetPreview({ onClose });
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should handle escape key to close', () => {
    const onClose = vi.fn();
    renderWidgetPreview({ onClose });
    
    fireEvent.keyDown(document, { key: 'Escape' });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should display widget toggle button', () => {
    renderWidgetPreview();
    
    const toggleButton = screen.getByRole('button', { name: /toggle widget/i });
    expect(toggleButton).toBeInTheDocument();
  });

  it('should toggle widget visibility', () => {
    renderWidgetPreview();
    
    const toggleButton = screen.getByRole('button', { name: /toggle widget/i });
    fireEvent.click(toggleButton);
    
    expect(screen.queryByText('Hi! How can I help you today?')).not.toBeInTheDocument();
  });

  it('should display widget in correct position', () => {
    renderWidgetPreview();
    
    const widget = screen.getByText('Customer Support').closest('div');
    expect(widget).toHaveClass('bottom-right');
  });

  it('should apply custom colors', () => {
    renderWidgetPreview();
    
    const widget = screen.getByText('Customer Support').closest('div');
    expect(widget).toHaveStyle({ '--primary-color': '#3b82f6' });
  });

  it('should display avatar when enabled', () => {
    renderWidgetPreview();
    
    const avatar = screen.getByAltText('Bot Avatar');
    expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg');
  });

  it('should not display avatar when disabled', () => {
    const configWithoutAvatar = {
      ...mockConfig,
      show_avatar: false,
    };
    
    renderWidgetPreview({ config: configWithoutAvatar });
    
    expect(screen.queryByAltText('Bot Avatar')).not.toBeInTheDocument();
  });

  it('should apply custom CSS', () => {
    renderWidgetPreview();
    
    const widget = screen.getByText('Customer Support').closest('div');
    expect(widget).toHaveClass('custom');
  });

  it('should respect max messages limit', () => {
    const configWithLimit = {
      ...mockConfig,
      max_messages: 2,
    };
    
    renderWidgetPreview({ config: configWithLimit });
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    
    // Send first message
    fireEvent.change(input, { target: { value: 'Message 1' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    // Send second message
    fireEvent.change(input, { target: { value: 'Message 2' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    // Try to send third message (should be blocked)
    fireEvent.change(input, { target: { value: 'Message 3' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(screen.queryByText('Message 3')).not.toBeInTheDocument();
  });

  it('should display message timestamps', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(screen.getByText(/Hello/)).toBeInTheDocument();
    // Timestamp should be displayed
    expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
  });

  it('should handle different themes', () => {
    const darkConfig = {
      ...mockConfig,
      theme: 'dark',
    };
    
    renderWidgetPreview({ config: darkConfig });
    
    const widget = screen.getByText('Customer Support').closest('div');
    expect(widget).toHaveClass('dark');
  });

  it('should handle different positions', () => {
    const leftConfig = {
      ...mockConfig,
      position: 'bottom-left',
    };
    
    renderWidgetPreview({ config: leftConfig });
    
    const widget = screen.getByText('Customer Support').closest('div');
    expect(widget).toHaveClass('bottom-left');
  });

  it('should display message count', () => {
    renderWidgetPreview();
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(screen.getByText('1/50')).toBeInTheDocument();
  });

  it('should handle widget resize', () => {
    renderWidgetPreview();
    
    const resizeHandle = screen.getByRole('button', { name: /resize/i });
    fireEvent.mouseDown(resizeHandle);
    
    // Should handle resize
    expect(resizeHandle).toBeInTheDocument();
  });

  it('should display widget settings', () => {
    renderWidgetPreview();
    
    const settingsButton = screen.getByRole('button', { name: /settings/i });
    fireEvent.click(settingsButton);
    
    expect(screen.getByText('Widget Settings')).toBeInTheDocument();
  });

  it('should handle sound toggle', () => {
    renderWidgetPreview();
    
    const soundToggle = screen.getByRole('checkbox', { name: /enable sound/i });
    fireEvent.click(soundToggle);
    
    expect(soundToggle).not.toBeChecked();
  });

  it('should handle typing indicator toggle', () => {
    renderWidgetPreview();
    
    const typingToggle = screen.getByRole('checkbox', { name: /enable typing indicator/i });
    fireEvent.click(typingToggle);
    
    expect(typingToggle).not.toBeChecked();
  });

  it('should handle websocket toggle', () => {
    renderWidgetPreview();
    
    const websocketToggle = screen.getByRole('checkbox', { name: /enable websocket/i });
    fireEvent.click(websocketToggle);
    
    expect(websocketToggle).not.toBeChecked();
  });

  it('should display widget code', () => {
    renderWidgetPreview();
    
    const codeButton = screen.getByRole('button', { name: /show code/i });
    fireEvent.click(codeButton);
    
    expect(screen.getByText('Embed Code')).toBeInTheDocument();
  });

  it('should copy embed code', () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
    
    renderWidgetPreview();
    
    const codeButton = screen.getByRole('button', { name: /show code/i });
    fireEvent.click(codeButton);
    
    const copyButton = screen.getByRole('button', { name: /copy code/i });
    fireEvent.click(copyButton);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });
});
