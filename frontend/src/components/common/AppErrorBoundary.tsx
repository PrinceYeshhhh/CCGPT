import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId?: string;
}

export class AppErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Generate a unique error ID for tracking
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return { hasError: true, error, errorId };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const isTestEnv = typeof process !== 'undefined' && process.env.NODE_ENV === 'test';
    
    // Log error for debugging
    if (!isTestEnv) {
      console.error('AppErrorBoundary caught an error:', error, errorInfo);
      
      // In production, you might want to send this to an error reporting service
      if (process.env.NODE_ENV === 'production') {
        // Example: Send to error reporting service
        // errorReportingService.captureException(error, {
        //   extra: errorInfo,
        //   tags: { component: 'AppErrorBoundary' }
        // });
      }
    }
    
    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    this.setState({ errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined, errorId: undefined });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReportBug = () => {
    const { error, errorId } = this.state;
    const bugReport = {
      errorId,
      message: error?.message,
      stack: error?.stack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };
    
    // In a real app, you'd send this to your bug reporting service
    console.log('Bug report:', bugReport);
    
    // For now, copy to clipboard
    navigator.clipboard.writeText(JSON.stringify(bugReport, null, 2))
      .then(() => alert('Bug report copied to clipboard'))
      .catch(() => alert('Failed to copy bug report'));
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorId } = this.state;
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
          <Card className="w-full max-w-2xl">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <CardTitle className="text-2xl">Something went wrong</CardTitle>
              <CardDescription className="text-lg">
                We're sorry, but something unexpected happened. Our team has been notified.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Error ID for support */}
              {errorId && (
                <div className="p-3 bg-gray-100 rounded-md text-center">
                  <p className="text-sm text-gray-600">
                    Error ID: <code className="font-mono">{errorId}</code>
                  </p>
                </div>
              )}

              {/* Development error details */}
              {isDevelopment && error && (
                <div className="p-4 bg-red-50 rounded-md border border-red-200">
                  <h4 className="font-semibold text-red-800 mb-2">Error Details (Development)</h4>
                  <pre className="text-xs text-red-700 overflow-auto max-h-40">
                    {error.message}
                    {error.stack && `\n\n${error.stack}`}
                  </pre>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button onClick={this.handleRetry} className="flex-1">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  onClick={this.handleGoHome}
                  className="flex-1"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
                <Button 
                  variant="outline" 
                  onClick={this.handleReportBug}
                  className="flex-1"
                >
                  <Bug className="w-4 h-4 mr-2" />
                  Report Bug
                </Button>
              </div>

              {/* Help text */}
              <div className="text-center text-sm text-gray-600">
                <p>If this problem persists, please contact support with the error ID above.</p>
                <p className="mt-1">
                  You can also try refreshing the page or clearing your browser cache.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
