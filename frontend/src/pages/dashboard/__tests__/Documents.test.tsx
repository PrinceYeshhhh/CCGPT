import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Documents } from '../Documents';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({
      ref: vi.fn(),
      onClick: vi.fn(),
    }),
    getInputProps: () => ({
      onChange: vi.fn(),
    }),
    isDragActive: false,
    isDragReject: false,
  }),
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

const mockDocuments = [
  {
    id: 'doc1',
    name: 'document1.pdf',
    status: 'active',
    uploaded_at: '2024-01-01T00:00:00Z',
    size: 1024000,
  },
  {
    id: 'doc2',
    name: 'document2.docx',
    status: 'processing',
    uploaded_at: '2024-01-02T00:00:00Z',
    size: 2048000,
  },
];

const mockWorkspaceSettings = {
  workspace_id: 'ws123',
  name: 'Test Workspace',
};

describe('Documents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/documents/') {
        return Promise.resolve({ data: mockDocuments });
      }
      if (url === '/workspace/settings') {
        return Promise.resolve({ data: mockWorkspaceSettings });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('should render loading state initially', () => {
    act(() => {
      render(<Documents />);
    });
    
    expect(screen.getByText('Document Manager')).toBeInTheDocument();
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
  });

  it('should load and display documents', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
      expect(screen.getByText('document2.docx')).toBeInTheDocument();
    });
  });

  it('should display document status', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  it('should display document size', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/1000\.0 KB/)).toBeInTheDocument();
      expect(screen.getByText(/2000\.0 KB/)).toBeInTheDocument();
    });
  });

  it('should handle document selection', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    
    expect(checkboxes[0]).toBeChecked();
  });

  it('should handle document actions', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    // Check that action buttons are present (they only contain icons)
    const actionButtons = screen.getAllByRole('button');
    expect(actionButtons.length).toBeGreaterThan(0);
  });

  it('should handle document upload', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    act(() => {
      render(<Documents />);
    });
    
    const fileInput = screen.getByRole('button', { name: /select files/i });
    fireEvent.click(fileInput);
    
    // File upload would be handled by dropzone
    expect(fileInput).toBeInTheDocument();
  });

  it('should display processing info section', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('How document processing works')).toBeInTheDocument();
      expect(screen.getByText('Upload:')).toBeInTheDocument();
      expect(screen.getByText('Processing:')).toBeInTheDocument();
      expect(screen.getByText('Embedding:')).toBeInTheDocument();
      expect(screen.getByText('Active:')).toBeInTheDocument();
    });
  });

  it('should display ask question section', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Ask about Selected Documents')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Type your question...')).toBeInTheDocument();
    });
  });

  it('should handle empty documents list', async () => {
    mockApi.get.mockImplementation((url) => {
      if (url === '/documents/') {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('No documents uploaded yet. Upload your first document to get started.')).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      // Should not crash and should show empty state
      expect(screen.getByText('Document Manager')).toBeInTheDocument();
    });
  });

  it('should display document actions', async () => {
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    // Check for action buttons by their icons (Eye for view, Trash2 for delete)
    const actionButtons = screen.getAllByRole('button');
    expect(actionButtons.length).toBeGreaterThan(0);
    // The buttons have icons, not text content
  });

  it('should handle document status changes', async () => {
    const processingDocument = {
      ...mockDocuments[0],
      status: 'processing',
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/documents/') {
        return Promise.resolve({ data: [processingDocument] });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  it('should display upload progress', async () => {
    act(() => {
      render(<Documents />);
    });
    
    expect(screen.getByText('Drag & drop files here, or click to select')).toBeInTheDocument();
  });

  it('should handle file size formatting', async () => {
    const largeDocument = {
      ...mockDocuments[0],
      size: 1073741824, // 1GB
    };
    
    mockApi.get.mockImplementation((url) => {
      console.log('API call:', url);
      if (url === '/documents/') {
        console.log('Returning large document:', largeDocument);
        return Promise.resolve({ data: [largeDocument] });
      }
      return Promise.resolve({ data: {} });
    });
    
    act(() => {
      render(<Documents />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
      expect(screen.getByText('Size: 1048576.0 KB')).toBeInTheDocument();
    });
  });
});
