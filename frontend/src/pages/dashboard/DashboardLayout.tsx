import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, Link } from 'react-router-dom';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { User, LogOut, Bell, Search, Menu, Settings, ChevronDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { DashboardAccessControl } from '@/components/dashboard/DashboardAccessControl';
import toast from 'react-hot-toast';

export function DashboardLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showVerifyBanner, setShowVerifyBanner] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showNotificationDropdown, setShowNotificationDropdown] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  React.useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/auth/me');
        const emailVerified = Boolean(res.data?.email_verified);
        setShowVerifyBanner(!emailVerified);
      } catch (e) {
        setShowVerifyBanner(false);
      }
    })();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      
      if (showUserDropdown && !target.closest('.user-dropdown')) {
        setShowUserDropdown(false);
      }
      
      if (showNotificationDropdown && !target.closest('.notification-dropdown')) {
        setShowNotificationDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserDropdown, showNotificationDropdown]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSettingsClick = () => {
    setShowUserDropdown(false);
    navigate('/dashboard/settings');
  };

  const handleNotificationClick = () => {
    setShowNotificationDropdown(!showNotificationDropdown);
    setShowUserDropdown(false);
  };

  // Mock notifications for now
  useEffect(() => {
    setNotifications([
      {
        id: 1,
        title: 'Welcome to CustomerCareGPT!',
        message: 'Your account has been successfully created.',
        time: '2 hours ago',
        read: false,
        type: 'info'
      },
      {
        id: 2,
        title: 'Usage Alert',
        message: 'You have used 80% of your monthly queries.',
        time: '1 day ago',
        read: false,
        type: 'warning'
      },
      {
        id: 3,
        title: 'New Feature Available',
        message: 'Check out the new analytics dashboard!',
        time: '3 days ago',
        read: true,
        type: 'success'
      }
    ]);
  }, []);

  return (
    <ErrorBoundary>
      <DashboardAccessControl>
        <div className="flex h-screen bg-background">
      <div className="hidden lg:block"><Sidebar /></div>
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black/40" onClick={() => setMobileOpen(false)} />
      )}
      <div className={"lg:hidden fixed z-50 inset-y-0 left-0 w-64 transform bg-card border-r border-border transition-transform " + (mobileOpen ? 'translate-x-0' : '-translate-x-full')}>
        <Sidebar />
      </div>
      
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="bg-card border-b border-border px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <button className="lg:hidden mr-2" onClick={() => setMobileOpen(true)} aria-label="Open sidebar">
                <Menu className="h-6 w-6" />
              </button>
              <div className="relative max-w-md w-full sm:w-auto">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 sm:h-4 sm:w-4 text-gray-400" />
                <Input 
                  placeholder="Search" 
                  className="pl-11 sm:pl-10 pr-4 w-full"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              <ThemeToggle />
              <div className="relative notification-dropdown">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="hidden sm:flex relative"
                  onClick={handleNotificationClick}
                >
                  <Bell className="h-5 w-5" />
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.filter(n => !n.read).length}
                    </span>
                  )}
                </Button>
                
                {showNotificationDropdown && (
                  <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-md shadow-lg z-50 border">
                    <div className="p-4 border-b">
                      <h3 className="text-lg font-semibold">Notifications</h3>
                    </div>
                    <div className="max-h-96 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-4 text-center text-gray-500">
                          No notifications
                        </div>
                      ) : (
                        notifications.map((notification) => (
                          <div
                            key={notification.id}
                            className={`p-4 border-b hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${
                              !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <div className={`w-2 h-2 rounded-full mt-2 ${
                                notification.type === 'warning' ? 'bg-yellow-500' :
                                notification.type === 'success' ? 'bg-green-500' :
                                'bg-blue-500'
                              }`} />
                              <div className="flex-1">
                                <h4 className="font-medium text-sm">{notification.title}</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {notification.message}
                                </p>
                                <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                    <div className="p-4 border-t">
                      <Button variant="outline" size="sm" className="w-full">
                        View All Notifications
                      </Button>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="hidden md:flex items-center space-x-3">
                <div className="text-right hidden lg:block">
                 <p className="text-sm font-medium text-foreground">{user?.full_name || user?.username || 'User'}</p>
                 <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                <div className="relative user-dropdown">
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    className="flex items-center space-x-1"
                  >
                    {user?.profile_picture_url ? (
                      <img 
                        src={user.profile_picture_url} 
                        alt="Profile" 
                        className="w-8 h-8 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                        {(user?.username || user?.email || 'U').charAt(0).toUpperCase()}
                      </div>
                    )}
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                  
                  {showUserDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg z-50 border">
                      <div className="py-1">
                        <div className="px-4 py-2 border-b">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.full_name || user?.username || 'User'}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
                        </div>
                        <button
                          onClick={handleSettingsClick}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <Settings className="mr-3 h-4 w-4" />
                          Settings
                        </button>
                        <button
                          onClick={handleLogout}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <LogOut className="mr-3 h-4 w-4" />
                          Sign out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Email verification banner */}
        {showVerifyBanner && (
          <div className="bg-yellow-50 border-b border-yellow-200 px-3 sm:px-6 py-3 text-yellow-900 text-sm flex items-center justify-between">
            <div>
              Your email is not verified. Please verify your email to unlock all features.
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={async () => {
                try {
                  await api.post('/auth/resend-verification');
                  toast.success('Verification email sent');
                } catch (e) {
                  toast.error('Failed to send verification email');
                }
              }}>Resend link</Button>
              <Button size="sm" variant="ghost" onClick={() => setShowVerifyBanner(false)}>Dismiss</Button>
            </div>
          </div>
        )}

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
      </div>
      </DashboardAccessControl>
    </ErrorBoundary>
  );
}