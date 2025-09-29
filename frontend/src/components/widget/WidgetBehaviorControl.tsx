import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface WidgetBehaviorControlProps {
  children: React.ReactNode;
  workspaceId: string;
}

interface SubscriptionStatus {
  plan: string;
  status: string;
  isTrial: boolean;
  trialEnd?: string;
}

export function WidgetBehaviorControl({ children, workspaceId }: WidgetBehaviorControlProps) {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSubscriptionStatus();
  }, [workspaceId]);

  const checkSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/billing/status');
      const billingInfo = response.data;
      
      setSubscription({
        plan: billingInfo.plan,
        status: billingInfo.status,
        isTrial: billingInfo.is_trial,
        trialEnd: billingInfo.trial_end
      });

      // Check if widget should be active
      const hasActiveSubscription = 
        billingInfo.plan === 'free_trial' && billingInfo.status === 'trialing' ||
        billingInfo.plan === 'starter' && billingInfo.status === 'active' ||
        billingInfo.plan === 'pro' && billingInfo.status === 'active' ||
        billingInfo.plan === 'enterprise' && billingInfo.status === 'active' ||
        billingInfo.plan === 'white_label' && billingInfo.status === 'active';

      setIsActive(hasActiveSubscription);

    } catch (error) {
      console.error('Failed to check subscription status:', error);
      // Default to inactive if we can't check
      setIsActive(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="w-14 h-14 bg-gray-300 dark:bg-gray-600 rounded-full animate-pulse"></div>
      </div>
    );
  }

  if (!isActive) {
    // Return inactive widget (dull, non-clickable)
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div 
          className="w-14 h-14 bg-gray-400 dark:bg-gray-700 rounded-full flex items-center justify-center cursor-not-allowed opacity-50"
          title="Widget inactive - subscription required"
        >
          <svg 
            className="w-6 h-6 text-gray-600 dark:text-gray-400" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
            />
          </svg>
        </div>
      </div>
    );
  }

  // Return active widget (glowing, clickable)
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div 
        className="w-14 h-14 bg-gradient-to-br from-[#4285F4] to-[#A142F4] rounded-full flex items-center justify-center cursor-pointer shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 animate-pulse"
        title="Click to chat with our AI assistant"
      >
        <svg 
          className="w-6 h-6 text-white" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
          />
        </svg>
      </div>
    </div>
  );
}
