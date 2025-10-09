import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  User, 
  Building, 
  Globe, 
  Shield, 
  Bell, 
  Palette,
  Upload,
  Trash2,
  Save,
  Eye,
  EyeOff,
  Key,
  AlertTriangle
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '@/lib/api';
import { z } from 'zod';
import toast from 'react-hot-toast';

const profileSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters').max(30, 'Username must be less than 30 characters'),
  email: z.string().email('Please enter a valid email address'),
  full_name: z.string().optional(),
  business_name: z.string().optional(),
  business_domain: z.string().optional(),
  profile_picture_url: z.string().optional(),
});

const organizationSchema = z.object({
  name: z.string().min(2, 'Organization name must be at least 2 characters'),
  description: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal('')),
  support_email: z.string().email().optional().or(z.literal('')),
  logo_url: z.string().optional(),
  custom_domain: z.string().optional(),
  widget_domain: z.string().optional(),
  timezone: z.string().default('UTC'),
});

const passwordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const teamMemberInviteSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  role: z.enum(['member', 'admin', 'owner']),
  message: z.string().optional(),
});

type ProfileForm = z.infer<typeof profileSchema>;
type OrganizationForm = z.infer<typeof organizationSchema>;
type PasswordForm = z.infer<typeof passwordSchema>;
type TeamMemberInviteForm = z.infer<typeof teamMemberInviteSchema>;

interface SettingsData {
  profile: ProfileForm;
  organization: OrganizationForm;
  notifications: {
    email_notifications: boolean;
    browser_notifications: boolean;
    usage_alerts: boolean;
    billing_updates: boolean;
    security_alerts: boolean;
    product_updates: boolean;
  };
  appearance: {
    theme: string;
    layout: string;
    language: string;
    timezone: string;
  };
  two_factor_enabled: boolean;
  team_members: Array<{
    id: number;
    email: string;
    full_name?: string;
    role: string;
    status: string;
    joined_at: string;
    last_active?: string;
  }>;
}

export function Settings({ hideHeader = false }: { hideHeader?: boolean }) {
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [notifications, setNotifications] = useState({
    email_notifications: true,
    browser_notifications: false,
    usage_alerts: true,
    billing_updates: true,
    security_alerts: true,
    product_updates: false
  });

  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      username: '',
      email: '',
      full_name: '',
      business_name: '',
      business_domain: '',
      profile_picture_url: ''
    }
  });

  const organizationForm = useForm({
    resolver: zodResolver(organizationSchema),
    defaultValues: {
      name: '',
      description: '',
      website_url: '',
      support_email: '',
      logo_url: '',
      custom_domain: '',
      widget_domain: '',
      timezone: 'UTC'
    }
  });

  const passwordForm = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  const teamMemberInviteForm = useForm({
    resolver: zodResolver(teamMemberInviteSchema),
    defaultValues: {
      email: '',
      role: 'member',
      message: ''
    }
  });

  // Fetch settings data
  React.useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setLoadError(null);
      const [settingsResp, userResp] = await Promise.all([
        api.get('/settings/'),
        api.get('/user/profile').catch(() => ({ data: {} })),
      ]);
      const data = settingsResp.data;
      
      setSettings(data);
      setNotifications(data.notifications);
      
      // Update form values
      const profileLike = (data.profile || data.user || userResp.data) as Partial<ProfileForm> | undefined;
      if (profileLike) profileForm.reset({
        username: profileLike.username || '',
        email: profileLike.email || '',
        full_name: profileLike.full_name || '',
        business_name: profileLike.business_name || '',
        business_domain: profileLike.business_domain || '',
        profile_picture_url: profileLike.profile_picture_url || ''
      });
      if (data.organization) organizationForm.reset(data.organization);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      setLoadError('Error loading settings');
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const onProfileSubmit = async (data: ProfileForm) => {
    try {
      await api.put('/user/profile', {
        full_name: data.full_name,
        business_name: data.business_name,
        business_domain: data.business_domain,
      });
      toast.success('Profile updated successfully!');
      fetchSettings(); // Refresh data
    } catch (error: any) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    }
  };

  const onOrganizationSubmit = async (data: OrganizationForm) => {
    try {
      await api.put('/organization/settings', {
        name: data.name,
        description: data.description,
        website_url: data.website_url,
        support_email: data.support_email,
        timezone: data.timezone,
        custom_domain: data.custom_domain,
        widget_domain: data.widget_domain,
      });
      toast.success('Organization updated successfully!');
      fetchSettings(); // Refresh data
    } catch (error: any) {
      console.error('Organization update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update organization');
    }
  };

  const onPasswordSubmit = async (data: PasswordForm) => {
    try {
      await api.put('/user/change-password', {
        current_password: data.currentPassword,
        new_password: data.newPassword,
        confirm_password: data.confirmPassword
      });
      toast.success('Password updated successfully!');
      passwordForm.reset();
    } catch (error: any) {
      console.error('Password update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update password');
    }
  };

  const onNotificationSubmit = async () => {
    try {
      await api.put('/settings/notifications', notifications);
      toast.success('Notification preferences updated!');
    } catch (error: any) {
      console.error('Notification update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update notifications');
    }
  };

  const onAppearanceSubmit = async (appearanceData: any) => {
    try {
      await api.put('/settings/appearance', appearanceData);
      toast.success('Appearance preferences updated!');
    } catch (error: any) {
      console.error('Appearance update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update appearance');
    }
  };

  const onTeamMemberInvite = async (data: any) => {
    try {
      await api.post('/settings/team/invite', data);
      toast.success('Team member invitation sent!');
      teamMemberInviteForm.reset();
      fetchSettings(); // Refresh team members
    } catch (error: any) {
      console.error('Team invite error:', error);
      toast.error(error.response?.data?.detail || 'Failed to send invitation');
    }
  };

  const handleFileUpload = async (file: File, type: 'profile' | 'organization') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const endpoint = type === 'profile' ? '/user/profile-picture' : '/organization/logo';
      const response = await api.put(endpoint, formData);
      
      const { url } = response.data;
      
      if (type === 'profile') {
        profileForm.setValue('profile_picture_url', url);
      } else {
        organizationForm.setValue('logo_url', url);
      }
      
      toast.success(`${type === 'profile' ? 'Profile picture' : 'Organization logo'} uploaded successfully!`);
    } catch (error: any) {
      console.error('File upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    }
  };

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      console.log('Account deletion requested');
      toast.error('Account deletion requested');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {!hideHeader && (
          <div className="flex justify-between items-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Settings</h1>
            <Badge variant="secondary">Loading...</Badge>
          </div>
        )}
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }
  if (loadError) {
    return (
      <div className="space-y-6">
        {!hideHeader && (
          <div className="flex justify-between items-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Settings</h1>
            <Badge variant="secondary">Error</Badge>
          </div>
        )}
        <div className="flex items-center justify-center h-64">
          <p>Error loading settings</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {!hideHeader && (
        <div className="flex justify-between items-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Settings</h1>
          <Badge variant="secondary">
            {settings?.profile?.business_name ? 
              `${settings.profile.business_name} - ${settings.profile.business_domain || 'No Domain'}` : 
              'Loading...'
            }
          </Badge>
        </div>
      )}

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">
            <User className="mr-2 h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="organization">
            <Building className="mr-2 h-4 w-4" />
            Organization
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="mr-2 h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="appearance">
            <Palette className="mr-2 h-4 w-4" />
            Appearance
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and contact details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-6">
                <div className="flex items-center space-x-6">
                  <div className="relative">
                    {profileForm.watch('profile_picture_url') ? (
                      <img 
                        src={profileForm.watch('profile_picture_url')} 
                        alt="Profile Picture" 
                        className="w-20 h-20 rounded-full object-cover"
                      />
                    ) : (
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {profileForm.watch('username')?.charAt(0)?.toUpperCase() || 'U'}
                    </div>
                    )}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileUpload(file, 'profile');
                      }}
                      className="hidden"
                      id="profile-picture-upload"
                    />
                    <Button size="sm" className="absolute -bottom-2 -right-2 rounded-full w-8 h-8 p-0" onClick={() => document.getElementById('profile-picture-upload')?.click()}>
                      <Upload className="h-4 w-4" />
                    </Button>
                  </div>
                  <div>
                    <h3 className="font-medium">Profile Picture</h3>
                    <p className="text-sm text-muted-foreground">
                      Upload a new profile picture. JPG, PNG or GIF (max 2MB)
                    </p>
                    <div className="mt-2 flex gap-2">
                      <Button type="button" variant="outline" onClick={() => document.getElementById('profile-picture-upload')?.click()}>Upload Photo</Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={async () => {
                          profileForm.setValue('profile_picture_url', '');
                          try {
                            await api.put('/user/profile', { profile_picture_url: null });
                            toast.success('Profile picture removed');
                          } catch (e) {
                            toast.error('Failed to remove photo');
                          }
                        }}
                      >
                        Remove Photo
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Username</label>
                    <Input
                      {...profileForm.register('username')}
                      placeholder="Enter your username"
                    />
                    {profileForm.formState.errors.username && (
                      <p className="text-red-600 text-sm">{profileForm.formState.errors.username.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email Address</label>
                    <Input
                      {...profileForm.register('email')}
                      type="email"
                      placeholder="Enter your email"
                    />
                    {profileForm.formState.errors.email && (
                      <p className="text-red-600 text-sm">{profileForm.formState.errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Full Name</label>
                    <Input
                      {...profileForm.register('full_name')}
                      placeholder="Enter your full name"
                    />
                    {profileForm.formState.errors.full_name && (
                      <p className="text-red-600 text-sm">{profileForm.formState.errors.full_name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Business Name</label>
                    <Input
                      {...profileForm.register('business_name')}
                      placeholder="Enter business name"
                    />
                    {profileForm.formState.errors.business_name && (
                      <p className="text-red-600 text-sm">{profileForm.formState.errors.business_name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Business Domain</label>
                    <Input
                      {...profileForm.register('business_domain')}
                      placeholder="company.com"
                    />
                    {profileForm.formState.errors.business_domain && (
                      <p className="text-red-600 text-sm">{profileForm.formState.errors.business_domain.message}</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={profileForm.formState.isSubmitting} className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110">
                    <Save className="mr-2 h-4 w-4" />
                    {profileForm.formState.isSubmitting ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="organization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Organization Settings</CardTitle>
              <CardDescription>
                Manage your organization's branding and domain settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={organizationForm.handleSubmit(onOrganizationSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Organization Name</label>
                    <Input
                      {...organizationForm.register('name')}
                      placeholder="Enter organization name"
                    />
                    {organizationForm.formState.errors.name && (
                      <p className="text-red-600 text-sm">{organizationForm.formState.errors.name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Website URL</label>
                    <Input
                      {...organizationForm.register('website_url')}
                      placeholder="https://yourcompany.com"
                    />
                    {organizationForm.formState.errors.website_url && (
                      <p className="text-red-600 text-sm">{organizationForm.formState.errors.website_url.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Support Email</label>
                    <Input
                      {...organizationForm.register('support_email')}
                      type="email"
                      placeholder="support@yourcompany.com"
                    />
                    {organizationForm.formState.errors.support_email && (
                      <p className="text-red-600 text-sm">{organizationForm.formState.errors.support_email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Timezone</label>
                    <select
                      {...organizationForm.register('timezone')}
                      className="w-full px-3 py-2 border border-input rounded-md"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Europe/Paris">Paris</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Description</label>
                  <textarea
                    {...organizationForm.register('description')}
                    placeholder="Enter organization description"
                    className="w-full px-3 py-2 border border-input rounded-md mt-2"
                    rows={3}
                  />
                </div>

              <div>
                <h3 className="font-medium mb-4">Organization Logo</h3>
                <div className="flex items-center space-x-4">
                    {organizationForm.watch('logo_url') ? (
                      <img 
                        src={organizationForm.watch('logo_url')} 
                        alt="Organization Logo" 
                        className="w-16 h-16 rounded-lg object-cover"
                      />
                    ) : (
                  <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center">
                    <Building className="h-8 w-8 text-muted-foreground" />
                  </div>
                    )}
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground mb-2">
                      Upload your organization logo. This will appear in your chat widget.
                    </p>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileUpload(file, 'organization');
                        }}
                        className="hidden"
                        id="organization-logo-upload"
                      />
                      <Button 
                        type="button"
                        variant="outline" 
                        size="sm"
                        onClick={() => document.getElementById('organization-logo-upload')?.click()}
                      >
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Logo
                    </Button>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-4">Custom Domain</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Widget Domain</label>
                    <Input 
                        {...organizationForm.register('widget_domain')}
                      placeholder="widget.yourcompany.com" 
                      className="mt-2"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Use your own domain for the chat widget (Pro plan feature)
                    </p>
                  </div>
                    <div>
                      <label className="text-sm font-medium">Custom Domain</label>
                      <Input 
                        {...organizationForm.register('custom_domain')}
                        placeholder="yourcompany.com" 
                        className="mt-2"
                      />
                    </div>
                    <Button type="button" variant="outline">
                    <Globe className="mr-2 h-4 w-4" />
                    Configure DNS
                  </Button>
                </div>
              </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={organizationForm.formState.isSubmitting} className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110">
                    <Save className="mr-2 h-4 w-4" />
                    {organizationForm.formState.isSubmitting ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>
                Manage your team members and their permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {settings?.team_members?.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {member.full_name?.charAt(0) || member.email.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{member.full_name || member.email}</p>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                      </div>
                    </div>
                    <Badge variant={member.role === 'owner' ? 'default' : 'secondary'}>
                      {member.role}
                    </Badge>
                  </div>
                ))}
                
                <form onSubmit={teamMemberInviteForm.handleSubmit(onTeamMemberInvite)} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium">Email</label>
                      <Input
                        {...teamMemberInviteForm.register('email')}
                        type="email"
                        placeholder="colleague@company.com"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Role</label>
                      <select
                        {...teamMemberInviteForm.register('role')}
                        className="w-full px-3 py-2 border border-input rounded-md"
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        <option value="owner">Owner</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      <Button type="submit" disabled={teamMemberInviteForm.formState.isSubmitting}>
                    <User className="mr-2 h-4 w-4" />
                        {teamMemberInviteForm.formState.isSubmitting ? 'Inviting...' : 'Invite Member'}
                  </Button>
                </div>
                  </div>
                </form>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>
                Update your password to keep your account secure
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Current Password</label>
                  <div className="relative">
                    <Input
                      {...passwordForm.register('currentPassword')}
                      type={showCurrentPassword ? 'text' : 'password'}
                      placeholder="Enter current password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-1/2 -translate-y-1/2"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    >
                      {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  {passwordForm.formState.errors.currentPassword && (
                    <p className="text-red-600 text-sm">{passwordForm.formState.errors.currentPassword.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">New Password</label>
                  <div className="relative">
                    <Input
                      {...passwordForm.register('newPassword')}
                      type={showNewPassword ? 'text' : 'password'}
                      placeholder="Enter new password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-2 top-1/2 -translate-y-1/2"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  {passwordForm.formState.errors.newPassword && (
                    <p className="text-red-600 text-sm">{passwordForm.formState.errors.newPassword.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Confirm New Password</label>
                  <Input
                    {...passwordForm.register('confirmPassword')}
                    type="password"
                    placeholder="Confirm new password"
                  />
                  {passwordForm.formState.errors.confirmPassword && (
                    <p className="text-red-600 text-sm">{passwordForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>

                <Button type="submit" disabled={passwordForm.formState.isSubmitting}>
                  <Key className="mr-2 h-4 w-4" />
                  {passwordForm.formState.isSubmitting ? 'Updating...' : 'Update Password'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Two-Factor Authentication</CardTitle>
              <CardDescription>
                Add an extra layer of security to your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Authenticator App</p>
                  <p className="text-sm text-muted-foreground">
                    Use an authenticator app to generate verification codes
                  </p>
                </div>
                <Button variant="outline">
                  Enable 2FA
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-200 dark:border-red-800">
            <CardHeader>
              <CardTitle className="text-red-600 dark:text-red-400">Danger Zone</CardTitle>
              <CardDescription>
                Irreversible and destructive actions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Delete Account</p>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all associated data
                  </p>
                </div>
                <Button variant="destructive" onClick={handleDeleteAccount}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Account
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Choose how you want to be notified about important updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Email Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Receive notifications via email
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.email_notifications}
                    onChange={(e) => setNotifications({...notifications, email_notifications: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Browser Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Show notifications in your browser
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.browser_notifications}
                    onChange={(e) => setNotifications({...notifications, browser_notifications: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Usage Alerts</p>
                    <p className="text-sm text-muted-foreground">
                      Get notified when approaching usage limits
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.usage_alerts}
                    onChange={(e) => setNotifications({...notifications, usage_alerts: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Billing Updates</p>
                    <p className="text-sm text-muted-foreground">
                      Notifications about billing and payments
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.billing_updates}
                    onChange={(e) => setNotifications({...notifications, billing_updates: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Security Alerts</p>
                    <p className="text-sm text-muted-foreground">
                      Important security-related notifications
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.security_alerts}
                    onChange={(e) => setNotifications({...notifications, security_alerts: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Product Updates</p>
                    <p className="text-sm text-muted-foreground">
                      New features and product announcements
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifications.product_updates}
                    onChange={(e) => setNotifications({...notifications, product_updates: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <Button onClick={onNotificationSubmit}>
                  <Save className="mr-2 h-4 w-4" />
                  Save Preferences
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Theme Preferences</CardTitle>
              <CardDescription>
                Customize the appearance of your dashboard
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-medium mb-4">Color Theme</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 border rounded-lg cursor-pointer hover:border-primary">
                    <div className="w-full h-20 bg-white border rounded mb-2"></div>
                    <p className="text-sm font-medium text-center">Light</p>
                  </div>
                  <div className="p-4 border rounded-lg cursor-pointer hover:border-primary">
                    <div className="w-full h-20 bg-gray-900 rounded mb-2"></div>
                    <p className="text-sm font-medium text-center">Dark</p>
                  </div>
                  <div className="p-4 border rounded-lg cursor-pointer hover:border-primary">
                    <div className="w-full h-20 bg-gradient-to-br from-white to-gray-900 rounded mb-2"></div>
                    <p className="text-sm font-medium text-center">System</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-4">Dashboard Layout</h3>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <input type="radio" name="layout" id="compact" className="w-4 h-4 text-blue-600 bg-background border-input" />
                    <label htmlFor="compact" className="text-sm text-foreground">Compact - More content in less space</label>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input type="radio" name="layout" id="comfortable" className="w-4 h-4 text-blue-600 bg-background border-input" defaultChecked />
                    <label htmlFor="comfortable" className="text-sm text-foreground">Comfortable - Balanced spacing</label>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input type="radio" name="layout" id="spacious" className="w-4 h-4 text-blue-600 bg-background border-input" />
                    <label htmlFor="spacious" className="text-sm text-foreground">Spacious - Extra breathing room</label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}