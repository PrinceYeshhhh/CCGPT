import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Embed } from '../Embed';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock WidgetPreview component
vi.mock('@/components/common/WidgetPreview', () => ({
  WidgetPreview: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="widget-preview">
        <div>Widget Preview</div>
        <button onClick={onClose}>Close Preview</button>
      </div>
    ) : null,
}));

// Mock Tabs components - simplified version that renders all content
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children }: any) => <div data-testid="tabs">{children}</div>,
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: any) => (
    <button data-testid={`tab-trigger-${value}`}>
      {children}
    </button>
  ),
  TabsContent: ({ children, value }: any) => (
    <div data-testid={`tab-content-${value}`}>
      {children}
    </div>
  ),
}));

const mockApi = vi.mocked(api);

const mockEmbedCodes = [
  {
    id: 'code1',
    code_name: 'Default Widget',
    embed_script: '<script src="https://example.com/widget.js"></script>',
    is_active: true,
    usage_count: 5,
  },
  {
    id: 'code2',
    code_name: 'Custom Widget',
    embed_script: '<script src="https://example.com/custom-widget.js"></script>',
    is_active: true,
    usage_count: 3,
  },
];

const mockWorkspaceSettings = {
  id: 'ws123',
  name: 'Test Workspace',
};

describe('Embed', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/embed/codes') {
        return Promise.resolve({ data: mockEmbedCodes });
      }
      if (url === '/workspace/settings') {
        return Promise.resolve({ data: mockWorkspaceSettings });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('should render loading state initially', () => {
    render(<Embed />);
    
    expect(screen.getByText('Embed Widget')).toBeInTheDocument(); 
    expect(screen.getByText('Generate Embed Code')).toBeInTheDocument();
  });

  it('should load and display embed codes', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Default Widget')).toBeInTheDocument();
      expect(screen.getByText('Custom Widget')).toBeInTheDocument();
    });
  });

  it('should display embed code', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Default Widget')).toBeInTheDocument();
    });
    
    // The component will use the embed_script from the mock data
    const codeElement = screen.getByText('<script src="https://example.com/widget.js"></script>');
    expect(codeElement).toBeInTheDocument();
  });

  it('should handle copy to clipboard', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
    
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Default Widget')).toBeInTheDocument();
    });
    
    const copyButtons = screen.getAllByText('Copy');
    fireEvent.click(copyButtons[0]);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('<script src="https://example.com/widget.js"></script>');
  });

  it('should display settings tabs', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
      expect(screen.getByText('Messages')).toBeInTheDocument();
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
  });

  it('should handle appearance settings', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    expect(screen.getByText('Primary Color')).toBeInTheDocument();
    expect(screen.getByText('Secondary Color')).toBeInTheDocument();
    expect(screen.getByText('Text Color')).toBeInTheDocument();
  });

  it('should handle messages settings', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Messages')).toBeInTheDocument();
    });
    
    const messagesTab = screen.getByText('Messages');
    fireEvent.click(messagesTab);
    
    expect(screen.getByText('Welcome Message')).toBeInTheDocument();
    expect(screen.getByText('Bot Name')).toBeInTheDocument();
    expect(screen.getByText('Placeholder Text')).toBeInTheDocument();
  });

  it('should handle behavior settings', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
    
    const behaviorTab = screen.getByText('Behavior');
    fireEvent.click(behaviorTab);
    
    expect(screen.getByText('Show typing indicator')).toBeInTheDocument();
    expect(screen.getByText('Sound notifications')).toBeInTheDocument();
  });

  it('should handle color input changes', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    const colorInputs = screen.getAllByDisplayValue('#3b82f6');
    const colorInput = colorInputs.find(input => input.type === 'text'); // Get the text input, not the color picker
    fireEvent.change(colorInput!, { target: { value: '#ff0000' } });
    
    expect(colorInput).toHaveValue('#ff0000');
  });

  it('should handle text input changes', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Messages')).toBeInTheDocument();
    });
    
    const messagesTab = screen.getByText('Messages');
    fireEvent.click(messagesTab);
    
    const welcomeInput = screen.getByDisplayValue('Hi! How can I help you today?');
    fireEvent.change(welcomeInput, { target: { value: 'Hello! How can I assist you?' } });
    
    expect(welcomeInput).toHaveValue('Hello! How can I assist you?');
  });

  it('should handle theme selection', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    // With simplified tabs mock, all content is always rendered
    // Find the theme select by looking for the option values
    const themeSelects = screen.getAllByRole('combobox');
    const themeSelect = themeSelects.find(select => 
      Array.from(select.querySelectorAll('option')).some(option => 
        option.textContent?.includes('Light')
      )
    );
    
    expect(themeSelect).toBeDefined();
    fireEvent.change(themeSelect!, { target: { value: 'dark' } });
    
    expect(themeSelect).toHaveValue('dark');
  });

  it('should handle position selection', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    // With simplified tabs mock, all content is always rendered
    // Find the position select by looking for the option values
    const positionSelects = screen.getAllByRole('combobox');
    const positionSelect = positionSelects.find(select => 
      Array.from(select.querySelectorAll('option')).some(option => 
        option.textContent?.includes('Bottom Right')
      )
    );
    
    expect(positionSelect).toBeDefined();
    fireEvent.change(positionSelect!, { target: { value: 'bottom-left' } });
    
    expect(positionSelect).toHaveValue('bottom-left');
  });

  it('should handle checkbox toggles', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
    
    // With simplified tabs mock, all content is always rendered
    expect(screen.getByText('Sound notifications')).toBeInTheDocument();
    
    const enableSoundCheckbox = screen.getByRole('checkbox', { name: /sound notifications/i });
    fireEvent.click(enableSoundCheckbox);
    
    expect(enableSoundCheckbox).not.toBeChecked();
  });

  it('should handle preview button', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Preview Widget')).toHaveLength(2);
    });
    
    // Click the second preview button (the one that opens the modal)
    const previewButtons = screen.getAllByText('Preview Widget');
    fireEvent.click(previewButtons[1]); // Click the second one
    
    expect(screen.getByTestId('widget-preview')).toBeInTheDocument();
  });

  it('should handle preview close', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Preview Widget')).toHaveLength(2);
    });
    
    const previewButtons = screen.getAllByText('Preview Widget');
    fireEvent.click(previewButtons[1]); // Click the second one
    
    expect(screen.getByTestId('widget-preview')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close Preview');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('widget-preview')).not.toBeInTheDocument();
  });

  it('should handle generate code', async () => {
    mockApi.post.mockResolvedValue({ data: { code: 'new-code' } });
    
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Generate Embed Code')).toBeInTheDocument();
    });
    
    const generateButton = screen.getByText('Generate Embed Code');
    fireEvent.click(generateButton);
    
    expect(mockApi.post).toHaveBeenCalled();
  });

  it('should handle workspace loading', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      // Workspace is loaded but not displayed in the UI
      expect(screen.getByText('Embed Widget')).toBeInTheDocument();
    });
  });

  it('should display custom CSS input', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    const cssTextarea = screen.getByPlaceholderText(':root { --ccgpt-primary: #4f46e5; }');
    fireEvent.change(cssTextarea, { target: { value: '.custom { color: red; }' } });
    
    expect(cssTextarea).toHaveValue('.custom { color: red; }');
  });

  it('should handle max messages input', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Messages')).toBeInTheDocument();
    });
    
    // With simplified tabs mock, all content is always rendered
    expect(screen.getByText('Max Messages Stored')).toBeInTheDocument();
    
    // Find the input by its type and value instead of label
    const maxMessagesInput = screen.getByDisplayValue('50');
    fireEvent.change(maxMessagesInput, { target: { value: '100' } });
    
    expect(maxMessagesInput).toHaveValue(100); // Expect number, not string
  });

  it('should handle API errors', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(<Embed />);
    
    await waitFor(() => {
      // Should not crash and should show empty state
      expect(screen.getByText('Embed Widget')).toBeInTheDocument();
    });
  });

  it('should display code generation status', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Generate Embed Code')).toBeInTheDocument();
    });
  });

  it('should handle empty embed codes', async () => {
    mockApi.get.mockImplementation((url) => {
      if (url === '/embed/codes') {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('No embed codes yet. Save changes below to generate one.')).toBeInTheDocument();
    });
  });
});
