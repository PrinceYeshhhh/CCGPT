import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Crown, Zap, Building, Star, Sparkles } from 'lucide-react';

interface CurrentPlanDisplayProps {
  plan: string;
  status: string;
  isTrial?: boolean;
  trialEnd?: string;
  className?: string;
}

export function CurrentPlanDisplay({ 
  plan, 
  status, 
  isTrial = false, 
  trialEnd,
  className = '' 
}: CurrentPlanDisplayProps) {
  const getPlanIcon = (planType: string) => {
    switch (planType) {
      case 'free_trial':
        return <Zap className="h-4 w-4" />;
      case 'starter':
        return <Star className="h-4 w-4" />;
      case 'pro':
        return <Crown className="h-4 w-4" />;
      case 'enterprise':
        return <Building className="h-4 w-4" />;
      case 'white_label':
        return <Sparkles className="h-4 w-4" />;
      default:
        return <Star className="h-4 w-4" />;
    }
  };

  const getPlanColor = (planType: string) => {
    switch (planType) {
      case 'free_trial':
        return 'bg-gradient-to-r from-green-500 to-blue-500 text-white';
      case 'starter':
        return 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white';
      case 'pro':
        return 'bg-gradient-to-r from-purple-500 to-pink-500 text-white';
      case 'enterprise':
        return 'bg-gradient-to-r from-orange-500 to-red-500 text-white';
      case 'white_label':
        return 'bg-gradient-to-r from-purple-600 to-pink-600 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getPlanName = (planType: string) => {
    switch (planType) {
      case 'free_trial':
        return 'Free Trial';
      case 'starter':
        return 'Starter';
      case 'pro':
        return 'Pro';
      case 'enterprise':
        return 'Enterprise';
      case 'white_label':
        return 'White Label';
      default:
        return 'Free';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'trialing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'canceled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const formatTrialEnd = (trialEnd: string) => {
    try {
      const date = new Date(trialEnd);
      const now = new Date();
      const diffTime = date.getTime() - now.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 0) {
        return 'Trial expired';
      } else if (diffDays === 1) {
        return '1 day left';
      } else {
        return `${diffDays} days left`;
      }
    } catch {
      return 'Trial active';
    }
  };

  return (
    <Card className={`${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${getPlanColor(plan)}`}>
              {getPlanIcon(plan)}
            </div>
            <div>
              <h3 className="font-semibold text-sm text-foreground">
                {getPlanName(plan)}
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                <Badge 
                  variant="secondary" 
                  className={`text-xs ${getStatusColor(status)}`}
                >
                  {status === 'trialing' ? 'Trial' : status.charAt(0).toUpperCase() + status.slice(1)}
                </Badge>
                {isTrial && trialEnd && (
                  <span className="text-xs text-muted-foreground">
                    {formatTrialEnd(trialEnd)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
