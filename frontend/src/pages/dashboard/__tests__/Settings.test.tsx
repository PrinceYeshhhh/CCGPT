import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Settings } from '../Settings';
import { api } from '@/lib/api';

// Mock the API
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock react-hook-form
vi.mock('react-hook-form', () => ({
  useForm: () => ({
    register: vi.fn(),
    handleSubmit: vi.fn((fn) => fn),
    formState: { errors: {} },
    watch: vi.fn(),
    setValue: vi.fn(),
    reset: vi.fn(),
  }),
}));

// Mock @hookform/resolvers/zod
vi.mock('@hookform/resolvers/zod', () => ({
  zodResolver: vi.fn(),
}));

const mockApi = vi.mocked(api);

const mockUserData = {
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  business_name: 'Test Business',
  business_domain: 'test.com',
  profile_picture_url: 'https://example.com/avatar.jpg',
};

const mockOrganizationData = {
  name: 'Test Organization',
  description: 'Test organization description',
  website_url: 'https://test.com',
  support_email: 'support@test.com',
  logo_url: 'https://example.com/logo.png',
  custom_domain: 'custom.test.com',
  widget_domain: 'widget.test.com',
  timezone: 'UTC',
};

const mockSettingsData = {
  user: mockUserData,
  organization: mockOrganizationData,
  team_members: [],
  notifications: {
    email_notifications: true,
    browser_notifications: false,
    usage_alerts: true,
    billing_updates: true,
    security_alerts: true,
    product_updates: false
  },
  preferences: {
    theme: 'light',
    language: 'en',
    timezone: 'UTC'
  }
};

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.get.mockImplementation((url) => {
      if (url === '/user/profile') {
        return Promise.resolve({ data: mockUserData });
      }
      if (url === '/organization/settings') {
        return Promise.resolve({ data: mockOrganizationData });
      }
      if (url === '/settings/') {
        return Promise.resolve({ data: mockSettingsData });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('should render settings page', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Profile')).toBeInTheDocument();
      expect(screen.getByText('Organization')).toBeInTheDocument();
      expect(screen.getByText('Security')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Appearance')).toBeInTheDocument();
    });
  });

  it('should display profile tab content', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Personal Information')).toBeInTheDocument();
      expect(screen.getByText('Username')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Full Name')).toBeInTheDocument();
    });
  });

  it('should display organization tab content', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const organizationTab = screen.getByText('Organization');
      fireEvent.click(organizationTab);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Organization Details')).toBeInTheDocument();
      expect(screen.getByText('Organization Name')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
      expect(screen.getByText('Website URL')).toBeInTheDocument();
    });
  });

  it('should display security tab content', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Security Settings')).toBeInTheDocument();
      expect(screen.getByText('Change Password')).toBeInTheDocument();
      expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument();
    });
  });

  it('should display notifications tab content', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const notificationsTab = screen.getByText('Notifications');
      fireEvent.click(notificationsTab);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
      expect(screen.getByText('Email Notifications')).toBeInTheDocument();
      expect(screen.getByText('Browser Notifications')).toBeInTheDocument();
    });
  });

  it('should display appearance tab content', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const appearanceTab = screen.getByText('Appearance');
      fireEvent.click(appearanceTab);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Appearance Settings')).toBeInTheDocument();
      expect(screen.getByText('Theme')).toBeInTheDocument();
      expect(screen.getByText('Language')).toBeInTheDocument();
    });
  });

  it('should handle profile update', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Profile updated successfully' } });
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      const fullNameInput = screen.getByDisplayValue('Test User');
      fireEvent.change(fullNameInput, { target: { value: 'Updated User' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile', {
      full_name: 'Updated User',
    });
  });

  it('should handle organization update', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Organization updated successfully' } });
    render(<Settings />);
    
    await waitFor(() => {
      const organizationTab = screen.getByText('Organization');
      fireEvent.click(organizationTab);
    });
    
    await waitFor(() => {
      const nameInput = screen.getByDisplayValue('Test Organization');
      fireEvent.change(nameInput, { target: { value: 'Updated Organization' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/organization/settings', {
      name: 'Updated Organization',
    });
  });

  it('should handle password change', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Password updated successfully' } });
    render(<Settings />);
    
    await waitFor(() => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);
    });
    
    await waitFor(() => {
      fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'oldpassword' } });
      fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpassword' } });
      fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpassword' } });
      fireEvent.click(screen.getByText('Change Password'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/password', {
      current_password: 'oldpassword',
      new_password: 'newpassword',
    });
  });

  it('should handle notification preferences update', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Notifications updated successfully' } });
    render(<Settings />);
    
    await waitFor(() => {
      const notificationsTab = screen.getByText('Notifications');
      fireEvent.click(notificationsTab);
    });
    
    await waitFor(() => {
      const emailCheckbox = screen.getByLabelText('Email Notifications');
      fireEvent.click(emailCheckbox);
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/settings/notifications', {
      email_notifications: false,
    });
  });

  it('should handle appearance settings update', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Appearance updated successfully' } });
    render(<Settings />);
    
    await waitFor(() => {
      const appearanceTab = screen.getByText('Appearance');
      fireEvent.click(appearanceTab);
    });
    
    await waitFor(() => {
      const themeSelect = screen.getByLabelText('Theme');
      fireEvent.change(themeSelect, { target: { value: 'dark' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/settings/preferences', {
      theme: 'dark',
    });
  });

  it('should handle profile picture upload', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Profile picture updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      const file = new File(['(⌐□_□)'], 'chucknorris.png', { type: 'image/png' });
      const input = screen.getByLabelText('Upload new picture');
      fireEvent.change(input, { target: { files: [file] } });
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/profile-picture', expect.any(FormData));
  });

  it('should handle organization logo upload', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Logo updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const organizationTab = screen.getByText('Organization');
      fireEvent.click(organizationTab);
    });
    
    await waitFor(() => {
      const file = new File(['(⌐□_□)'], 'logo.png', { type: 'image/png' });
      const input = screen.getByLabelText('Upload new logo');
      fireEvent.change(input, { target: { files: [file] } });
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/organization/logo', expect.any(FormData));
  });

  it('should handle two-factor authentication toggle', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: '2FA updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);
    });
    
    await waitFor(() => {
      const twoFactorToggle = screen.getByLabelText('Enable Two-Factor Authentication');
      fireEvent.click(twoFactorToggle);
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/user/2fa', {
      enabled: true,
    });
  });

  it('should handle API key generation', async () => {
    mockApi.post.mockResolvedValueOnce({ data: { api_key: 'new-api-key' } });
    render(<Settings />);
    
    await waitFor(() => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);
    });
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Generate New API Key'));
    });
    
    expect(mockApi.post).toHaveBeenCalledWith('/user/api-keys');
  });

  it('should handle API key deletion', async () => {
    mockApi.delete.mockResolvedValueOnce({ data: { message: 'API key deleted' } });
    render(<Settings />);
    
    await waitFor(() => {
      const securityTab = screen.getByText('Security');
      fireEvent.click(securityTab);
    });
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Delete API Key'));
    });
    
    expect(mockApi.delete).toHaveBeenCalledWith('/user/api-keys/1');
  });

  it('should handle theme selection', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Theme updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const appearanceTab = screen.getByText('Appearance');
      fireEvent.click(appearanceTab);
    });
    
    await waitFor(() => {
      const themeSelect = screen.getByLabelText('Theme');
      fireEvent.change(themeSelect, { target: { value: 'dark' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/settings/preferences', {
      theme: 'dark',
    });
  });

  it('should handle language selection', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Language updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const appearanceTab = screen.getByText('Appearance');
      fireEvent.click(appearanceTab);
    });
    
    await waitFor(() => {
      const languageSelect = screen.getByLabelText('Language');
      fireEvent.change(languageSelect, { target: { value: 'es' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/settings/preferences', {
      language: 'es',
    });
  });

  it('should handle notification toggle', async () => {
    mockApi.put.mockResolvedValueOnce({ data: { message: 'Notifications updated' } });
    render(<Settings />);
    
    await waitFor(() => {
      const notificationsTab = screen.getByText('Notifications');
      fireEvent.click(notificationsTab);
    });
    
    await waitFor(() => {
      const emailCheckbox = screen.getByLabelText('Email Notifications');
      fireEvent.click(emailCheckbox);
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(mockApi.put).toHaveBeenCalledWith('/settings/notifications', {
      email_notifications: false,
    });
  });

  it('should handle form validation errors', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      const emailInput = screen.getByDisplayValue('test@example.com');
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(screen.getByText('Invalid email address')).toBeInTheDocument();
    expect(mockApi.put).not.toHaveBeenCalled();
  });

  it('should handle API errors', async () => {
    mockApi.put.mockRejectedValueOnce({ response: { data: { error: 'API Error' } } });
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      const fullNameInput = screen.getByDisplayValue('Test User');
      fireEvent.change(fullNameInput, { target: { value: 'Error User' } });
      fireEvent.click(screen.getByText('Save Changes'));
    });
    
    expect(screen.getByText('API Error')).toBeInTheDocument();
  });

  it('should display current user data', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const profileTab = screen.getByText('Profile');
      fireEvent.click(profileTab);
    });
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    });
  });

  it('should display current organization data', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      const organizationTab = screen.getByText('Organization');
      fireEvent.click(organizationTab);
    });
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Organization')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test organization description')).toBeInTheDocument();
      expect(screen.getByDisplayValue('https://test.com')).toBeInTheDocument();
    });
  });

  it('should handle loading state', () => {
    mockApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<Settings />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should handle error state', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('Network error'));
    render(<Settings />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading settings')).toBeInTheDocument();
    });
  });
});