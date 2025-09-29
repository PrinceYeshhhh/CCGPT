import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Code, 
  BarChart3, 
  CreditCard, 
  Settings,
  Bot,
  Activity,
  ArrowUpRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTheme } from '@/contexts/ThemeContext';
import { api } from '@/lib/api';

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Documents', href: '/dashboard/documents', icon: FileText },
  { name: 'Embed Widget', href: '/dashboard/embed', icon: Code },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Performance', href: '/dashboard/performance', icon: Activity },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [billingInfo, setBillingInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingInfo();
  }, []);

  const fetchBillingInfo = async () => {
    try {
      const response = await api.get('/billing/status');
      setBillingInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch billing info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  return (
    <div className="hidden lg:flex flex-col w-64 bg-card border-r border-border min-h-screen">
      {/* Logo */}
      <div className="flex items-center px-6 py-4 border-b">
        <Bot className="h-8 w-8 text-blue-600" />
        <span className="ml-2 text-lg font-semibold text-foreground">CustomerCareGPT</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm rounded-md transition-all duration-200',
                isActive
                  ? 'bg-[#4285F4]/10 text-black hover:text-black dark:text-white dark:hover:text-white border-l-4 border-[#4285F4] shadow-sm font-semibold'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
              style={isActive ? { color: theme === 'dark' ? '#ffffff' : '#000000' } : undefined}
            >
              <item.icon 
                className={cn('mr-3 h-5 w-5')}
                style={isActive ? { color: theme === 'dark' ? '#ffffff' : '#000000' } : undefined}
              />
              <span className={cn(isActive ? undefined : undefined)}>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Plan Info */}
      <div className="px-4 py-4 border-t">
        <div className="rounded-lg p-3 text-white bg-gradient-to-br from-[#4285F4] to-[#A142F4]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">
                {loading ? 'Loading...' : 
                 billingInfo?.plan ? 
                   `${billingInfo.plan.charAt(0).toUpperCase() + billingInfo.plan.slice(1)} Plan` : 
                   'Free Plan'
                }
              </p>
              <p className="text-xs opacity-90">
                {loading ? 'Loading...' : 
                 billingInfo?.usage ? 
                   `${billingInfo.usage.queries_used.toLocaleString()} / ${billingInfo.usage.queries_limit === -1 ? '∞' : billingInfo.usage.queries_limit.toLocaleString()} queries` : 
                   '0 / 100 queries'
                }
              </p>
            </div>
            <button 
              onClick={handleUpgrade}
              className="text-xs bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded transition-colors flex items-center"
            >
              Upgrade
              <ArrowUpRight className="ml-1 h-3 w-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}