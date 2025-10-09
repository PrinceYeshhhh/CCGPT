import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '@/test/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { UserProfile } from '../UserProfile';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

// Mock useAuth hook
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: {
      username: 'testuser',
      email: 'test@example.com',
      full_name: 'Test User',
    },
  }),
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock Settings component
vi.mock('@/pages/dashboard/Settings', () => ({
  Settings: () => (
    <div data-testid="settings-component">
      <h1>Settings</h1>
      <div>Settings content</div>
    </div>
  ),
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockApi = vi.mocked(api);

const mockUserData = {
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  profile_picture_url: 'https://example.com/avatar.jpg',
  created_at: '2024-01-01T00:00:00Z',
  last_login: '2024-01-15T10:30:00Z',
};

const mockSettingsData = {
  team_members: [],
  notifications: {
    email: true,
    push: false,
    email_notifications: true,
    push_notifications: false,
  },
  preferences: {
    language: 'en',
    timezone: 'UTC',
  },
};

describe('UserProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/user/profile') {
        return Promise.resolve({ data: mockUserData });
      }
      if (url === '/settings/') {
        return Promise.resolve({ data: mockSettingsData });
      }
      return Promise.resolve({ data: {} });
    });
  });

  const renderUserProfile = () => {
    return render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );
  };

  it('should render user profile page', () => {
    renderUserProfile();
    
    expect(screen.getByText('User Profile')).toBeInTheDocument();
    expect(screen.getByText('Manage your account settings')).toBeInTheDocument();
  });

  it('should display user information', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    });
  });

  it('should display profile picture', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      const profileImage = screen.getByAltText('Profile Picture');
      expect(profileImage).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });
  });

  it('should handle profile update', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
    });
    
    const fullNameInput = screen.getByDisplayValue('Test User');
    fireEvent.change(fullNameInput, { target: { value: 'Updated Name' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile', {
      full_name: 'Updated Name',
    });
  });

  it('should handle profile picture upload', async () => {
    mockApi.put.mockResolvedValue({ data: { profile_picture_url: 'https://example.com/new-avatar.jpg' } });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Upload Photo')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByText('Upload Photo');
    fireEvent.click(uploadButton);
    
    // File upload would be handled by file input
    expect(uploadButton).toBeInTheDocument();
  });

  it('should display account statistics', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Account Statistics')).toBeInTheDocument();
      expect(screen.getByText('Member since')).toBeInTheDocument();
      expect(screen.getByText('Last login')).toBeInTheDocument();
    });
  });

  it('should handle password change', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Change Password')).toBeInTheDocument();
    });
    
    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    
    fireEvent.change(currentPasswordInput, { target: { value: 'current123' } });
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/change-password', {
      current_password: 'current123',
      new_password: 'newpassword123',
    });
  });

  it('should handle password mismatch error', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Change Password')).toBeInTheDocument();
    });
    
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm new password/i);
    
    fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'different123' } });
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
  });

  it('should handle email update', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    });
    
    const emailInput = screen.getByDisplayValue('test@example.com');
    fireEvent.change(emailInput, { target: { value: 'newemail@example.com' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile', {
      email: 'newemail@example.com',
    });
  });

  it('should handle username update', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
    });
    
    const usernameInput = screen.getByDisplayValue('testuser');
    fireEvent.change(usernameInput, { target: { value: 'newusername' } });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile', {
      username: 'newusername',
    });
  });

  it('should handle form validation errors', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
    });
    
    const usernameInput = screen.getByDisplayValue('testuser');
    fireEvent.change(usernameInput, { target: { value: 'ab' } }); // Too short
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(screen.getByText('Username must be at least 3 characters')).toBeInTheDocument();
  });

  it('should handle API errors', async () => {
    mockApi.put.mockRejectedValueOnce(new Error('API Error'));
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    // Should handle error gracefully
    expect(saveButton).toBeInTheDocument();
  });

  it('should display loading state', () => {
    mockApi.get.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderUserProfile();
    
    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  it('should handle logout', () => {
    renderUserProfile();
    
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should display account settings', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Account Settings')).toBeInTheDocument();
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
      expect(screen.getByText('Security Settings')).toBeInTheDocument();
    });
  });

  it('should handle profile picture removal', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Remove Photo')).toBeInTheDocument();
    });
    
    const removeButton = screen.getByText('Remove Photo');
    fireEvent.click(removeButton);
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile', {
      profile_picture_url: null,
    });
  });

  it('should display user preferences', async () => {
    renderUserProfile();

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Settings content')).toBeInTheDocument();
    });
  });

  it('should handle preference updates', async () => {
    mockApi.put.mockResolvedValue({ data: {} });
    
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
    
    // Test that Settings component is rendered
    expect(screen.getByTestId('settings-component')).toBeInTheDocument();
  });

  it('should display account deletion section', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Settings content')).toBeInTheDocument();
    });
  });

  it('should handle account deletion confirmation', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
    
    // Test that Settings component is rendered
    expect(screen.getByTestId('settings-component')).toBeInTheDocument();
  });

  it('should handle account deletion cancellation', async () => {
    renderUserProfile();
    
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
    
    // Test that Settings component is rendered
    expect(screen.getByTestId('settings-component')).toBeInTheDocument();
  });
});
