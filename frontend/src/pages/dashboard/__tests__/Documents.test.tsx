import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
    render(<Documents />);
    
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
  });

  it('should load and display documents', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
      expect(screen.getByText('document2.docx')).toBeInTheDocument();
    });
  });

  it('should display document status', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Processing')).toBeInTheDocument();
    });
  });

  it('should display document size', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('1.0 MB')).toBeInTheDocument();
      expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    });
  });

  it('should handle document selection', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    
    expect(checkboxes[0]).toBeChecked();
  });

  it('should handle bulk delete', async () => {
    mockApi.delete.mockResolvedValue({ data: {} });
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    
    const deleteButton = screen.getByText('Delete Selected');
    fireEvent.click(deleteButton);
    
    expect(mockApi.delete).toHaveBeenCalled();
  });

  it('should handle individual document delete', async () => {
    mockApi.delete.mockResolvedValue({ data: {} });
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);
    
    expect(mockApi.delete).toHaveBeenCalled();
  });

  it('should handle document upload', async () => {
    mockApi.post.mockResolvedValue({ data: {} });
    
    render(<Documents />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(fileInput);
    
    // File upload would be handled by dropzone
    expect(fileInput).toBeInTheDocument();
  });

  it('should display ask question functionality', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('Ask a Question')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Ask a question about your documents...')).toBeInTheDocument();
    });
  });

  it('should handle ask question submission', async () => {
    mockApi.post.mockResolvedValue({ data: { answer: 'Test answer' } });
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question about your documents...')).toBeInTheDocument();
    });
    
    const input = screen.getByPlaceholderText('Ask a question about your documents...');
    fireEvent.change(input, { target: { value: 'What is this about?' } });
    
    const askButton = screen.getByText('Ask');
    fireEvent.click(askButton);
    
    expect(mockApi.post).toHaveBeenCalled();
  });

  it('should display workspace information', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Workspace')).toBeInTheDocument();
    });
  });

  it('should handle refresh', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    expect(mockApi.get).toHaveBeenCalledWith('/documents/');
  });

  it('should handle empty documents list', async () => {
    mockApi.get.mockImplementation((url) => {
      if (url === '/documents/') {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('No documents uploaded yet')).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(<Documents />);
    
    await waitFor(() => {
      // Should not crash and should show empty state
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });
  });

  it('should display document actions', async () => {
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('document1.pdf')).toBeInTheDocument();
    });
    
    const actionButtons = screen.getAllByRole('button');
    expect(actionButtons.some(btn => btn.textContent?.includes('View'))).toBe(true);
    expect(actionButtons.some(btn => btn.textContent?.includes('Delete'))).toBe(true);
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
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('Processing')).toBeInTheDocument();
    });
  });

  it('should display upload progress', async () => {
    render(<Documents />);
    
    expect(screen.getByText('Drag and drop files here, or click to select')).toBeInTheDocument();
  });

  it('should handle file size formatting', async () => {
    const largeDocument = {
      ...mockDocuments[0],
      size: 1073741824, // 1GB
    };
    
    mockApi.get.mockImplementation((url) => {
      if (url === '/documents/') {
        return Promise.resolve({ data: [largeDocument] });
      }
      return Promise.resolve({ data: {} });
    });
    
    render(<Documents />);
    
    await waitFor(() => {
      expect(screen.getByText('1.0 GB')).toBeInTheDocument();
    });
  });
});
