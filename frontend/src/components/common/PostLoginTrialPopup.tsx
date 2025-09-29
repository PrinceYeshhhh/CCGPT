import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Gift, Clock, FileText, MessageSquare, Zap } from 'lucide-react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

interface PostLoginTrialPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function PostLoginTrialPopup({ isOpen, onClose, onSuccess }: PostLoginTrialPopupProps) {
  const [loading, setLoading] = useState(false);

  const handleStartTrial = async () => {
    setLoading(true);
    try {
      // Get current user info first
      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;
      
      const response = await api.post('/pricing/start-trial', {
        email: user.email,
        mobile_phone: user.mobile_phone || ''
      });

      if (response.data.success) {
        toast.success('Free trial started successfully!');
        onSuccess();
        onClose();
      } else {
        toast.error(response.data.message || 'Failed to start trial');
      }
    } catch (error: any) {
      console.error('Failed to start trial:', error);
      toast.error(error.response?.data?.message || 'Failed to start trial');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center mb-4">
            <Gift className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to CustomerCareGPT!</CardTitle>
          <CardDescription className="text-lg">
            Start your 7-day free trial and experience the power of AI customer support
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Trial Benefits */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center">
              <Zap className="mr-2 h-5 w-5 text-yellow-500" />
              What you get with your free trial:
            </h3>
            
            <div className="grid grid-cols-1 gap-3">
              <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-green-800 dark:text-green-200">7 days completely free</p>
                  <p className="text-sm text-green-600 dark:text-green-400">No credit card required</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                <MessageSquare className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-200">100 AI queries included</p>
                  <p className="text-sm text-blue-600 dark:text-blue-400">Test all features thoroughly</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
                <FileText className="h-5 w-5 text-purple-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-purple-800 dark:text-purple-200">1 document upload</p>
                  <p className="text-sm text-purple-600 dark:text-purple-400">Train your AI assistant</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-3 bg-orange-50 dark:bg-orange-950 rounded-lg">
                <Clock className="h-5 w-5 text-orange-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-orange-800 dark:text-orange-200">Full dashboard access</p>
                  <p className="text-sm text-orange-600 dark:text-orange-400">Analytics, settings, and more</p>
                </div>
              </div>
            </div>
          </div>

          {/* Trial Status Badge */}
          <div className="text-center">
            <Badge variant="secondary" className="text-sm px-4 py-2">
              <Clock className="mr-1 h-4 w-4" />
              One-time offer - Start now!
            </Badge>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleStartTrial}
              className="w-full bg-gradient-to-br from-green-600 to-blue-600 text-white border-0 hover:brightness-110"
              disabled={loading}
              size="lg"
            >
              {loading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Starting Trial...
                </>
              ) : (
                <>
                  <Gift className="mr-2 h-5 w-5" />
                  Start Free Trial
                </>
              )}
            </Button>
            
            <Button
              onClick={onClose}
              variant="outline"
              className="w-full"
              disabled={loading}
            >
              Maybe Later
            </Button>
          </div>

          <p className="text-xs text-center text-muted-foreground">
            By starting the trial, you agree to our Terms of Service and Privacy Policy.
            You can cancel anytime during the trial period.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
