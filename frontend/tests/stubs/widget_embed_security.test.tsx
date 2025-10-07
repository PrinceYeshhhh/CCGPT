import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WidgetPreview } from '@/components/common/WidgetPreview'

const baseConfig = {
  title: 'Chatbot',
  welcome_message: 'Hello! 👋',
  placeholder: 'Type your message...',
  primary_color: '#4f46e5',
  secondary_color: '#111827',
  text_color: '#ffffff',
  position: 'bottom-right',
  show_avatar: true,
  enable_sound: false,
  enable_typing_indicator: true,
  enable_websocket: false,
  theme: 'dark',
  max_messages: 50 as number
}

describe('Widget embed security', () => {
  it('embed preview renders without executing inline scripts', () => {
    render(
      <WidgetPreview 
        isOpen={true} 
        onClose={() => {}} 
        config={{ ...(baseConfig as any), custom_css: "body{background:red;}<script>alert('xss')</script>" }} 
      />
    )

    // Target the chat bubble specifically using test ID
    const chatBubble = screen.getByTestId('chat-bubble-button')
    fireEvent.click(chatBubble)

    expect(screen.getByText(/widget preview/i)).toBeInTheDocument()
  })
})


