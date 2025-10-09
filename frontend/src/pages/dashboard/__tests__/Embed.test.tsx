import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
  WidgetPreview: ({ settings, onClose }: any) => (
    <div data-testid="widget-preview">
      <div>Widget Preview</div>
      <button onClick={onClose}>Close Preview</button>
    </div>
  ),
}));

const mockApi = vi.mocked(api);

const mockEmbedCodes = [
  {
    id: 'code1',
    name: 'Default Widget',
    code: '<script src="https://example.com/widget.js"></script>',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'code2',
    name: 'Custom Widget',
    code: '<script src="https://example.com/custom-widget.js"></script>',
    created_at: '2024-01-02T00:00:00Z',
  },
];

const mockWorkspaceSettings = {
  workspace_id: 'ws123',
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
    expect(screen.getByText('Generate Code')).toBeInTheDocument();
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
      expect(screen.getByText('Behavior')).toBeInTheDocument();
      expect(screen.getByText('Advanced')).toBeInTheDocument();
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

  it('should handle behavior settings', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
    
    const behaviorTab = screen.getByText('Behavior');
    fireEvent.click(behaviorTab);
    
    expect(screen.getByText('Welcome Message')).toBeInTheDocument();
    expect(screen.getByText('Bot Name')).toBeInTheDocument();
    expect(screen.getByText('Placeholder Text')).toBeInTheDocument();
  });

  it('should handle advanced settings', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Advanced')).toBeInTheDocument();
    });
    
    const advancedTab = screen.getByText('Advanced');
    fireEvent.click(advancedTab);
    
    expect(screen.getByText('Custom CSS')).toBeInTheDocument();
    expect(screen.getByText('Max Messages')).toBeInTheDocument();
  });

  it('should handle color input changes', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    const colorInput = screen.getByDisplayValue('#3b82f6');
    fireEvent.change(colorInput, { target: { value: '#ff0000' } });
    
    expect(colorInput).toHaveValue('#ff0000');
  });

  it('should handle text input changes', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
    
    const behaviorTab = screen.getByText('Behavior');
    fireEvent.click(behaviorTab);
    
    const welcomeInput = screen.getByDisplayValue('Hi! How can I help you today?');
    fireEvent.change(welcomeInput, { target: { value: 'Hello! How can I assist you?' } });
    
    expect(welcomeInput).toHaveValue('Hello! How can I assist you?');
  });

  it('should handle theme selection', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    const themeSelect = screen.getByDisplayValue('light');
    fireEvent.change(themeSelect, { target: { value: 'dark' } });
    
    expect(themeSelect).toHaveValue('dark');
  });

  it('should handle position selection', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
    
    const appearanceTab = screen.getByText('Appearance');
    fireEvent.click(appearanceTab);
    
    const positionSelect = screen.getByDisplayValue('bottom-right');
    fireEvent.change(positionSelect, { target: { value: 'bottom-left' } });
    
    expect(positionSelect).toHaveValue('bottom-left');
  });

  it('should handle checkbox toggles', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Behavior')).toBeInTheDocument();
    });
    
    const behaviorTab = screen.getByText('Behavior');
    fireEvent.click(behaviorTab);
    
    const enableSoundCheckbox = screen.getByRole('checkbox', { name: /enable sound/i });
    fireEvent.click(enableSoundCheckbox);
    
    expect(enableSoundCheckbox).not.toBeChecked();
  });

  it('should handle preview button', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Preview Widget')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview Widget');
    fireEvent.click(previewButton);
    
    expect(screen.getByTestId('widget-preview')).toBeInTheDocument();
  });

  it('should handle preview close', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Preview Widget')).toBeInTheDocument();
    });
    
    const previewButton = screen.getByText('Preview Widget');
    fireEvent.click(previewButton);
    
    expect(screen.getByTestId('widget-preview')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close Preview');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('widget-preview')).not.toBeInTheDocument();
  });

  it('should handle generate code', async () => {
    mockApi.post.mockResolvedValue({ data: { code: 'new-code' } });
    
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Generate Code')).toBeInTheDocument();
    });
    
    const generateButton = screen.getByText('Generate Code');
    fireEvent.click(generateButton);
    
    expect(mockApi.post).toHaveBeenCalled();
  });

  it('should handle workspace selection', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Workspace')).toBeInTheDocument();
    });
  });

  it('should display custom CSS input', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Advanced')).toBeInTheDocument();
    });
    
    const advancedTab = screen.getByText('Advanced');
    fireEvent.click(advancedTab);
    
    const cssTextarea = screen.getByPlaceholderText('Enter custom CSS...');
    fireEvent.change(cssTextarea, { target: { value: '.custom { color: red; }' } });
    
    expect(cssTextarea).toHaveValue('.custom { color: red; }');
  });

  it('should handle max messages input', async () => {
    render(<Embed />);
    
    await waitFor(() => {
      expect(screen.getByText('Advanced')).toBeInTheDocument();
    });
    
    const advancedTab = screen.getByText('Advanced');
    fireEvent.click(advancedTab);
    
    const maxMessagesInput = screen.getByDisplayValue('50');
    fireEvent.change(maxMessagesInput, { target: { value: '100' } });
    
    expect(maxMessagesInput).toHaveValue('100');
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
      expect(screen.getByText('Generate Code')).toBeInTheDocument();
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
      expect(screen.getByText('No embed codes generated yet')).toBeInTheDocument();
    });
  });
});
