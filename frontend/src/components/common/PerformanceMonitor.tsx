import React, { useEffect } from 'react';
import { usePerformance } from '@/hooks/usePerformance';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Activity, Zap, AlertTriangle, CheckCircle, Clock, Cpu, MousePointer } from 'lucide-react';

interface PerformanceMonitorProps {
  showDetails?: boolean;
  className?: string;
}

export function PerformanceMonitor({ showDetails = false, className = '' }: PerformanceMonitorProps) {
  const { 
    metrics, 
    isLoading, 
    error, 
    getPerformanceSummary, 
    getPerformanceScore 
  } = usePerformance({
    enableWebVitals: true,
    enableCustomMetrics: true,
    enableUserTracking: true,
    enableErrorTracking: true,
    reportInterval: 30000, // 30 seconds
  });

  const summary = getPerformanceSummary();
  const score = getPerformanceScore();

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default';
    if (score >= 70) return 'secondary';
    return 'destructive';
  };

  const getHealthIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (score >= 70) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <AlertTriangle className="h-4 w-4 text-red-600" />;
  };

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Performance Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-red-600 text-sm">
            Failed to load performance data: {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Performance Monitor
          {isLoading && <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />}
        </CardTitle>
        <CardDescription>
          Real-time performance metrics and Core Web Vitals
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Performance Score */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getHealthIcon(score)}
            <span className="font-medium">Performance Score</span>
          </div>
          <Badge variant={getScoreBadgeVariant(score)} className="text-sm">
            {score}/100
          </Badge>
        </div>
        <Progress value={score} className="h-2" />

        {/* Core Web Vitals */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <Zap className="h-4 w-4 text-blue-600" />
              <span>LCP</span>
            </div>
            <div className="text-lg font-semibold">{summary.lcp}</div>
            <div className="text-xs text-gray-500">Largest Contentful Paint</div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <MousePointer className="h-4 w-4 text-green-600" />
              <span>FID</span>
            </div>
            <div className="text-lg font-semibold">{summary.fid}</div>
            <div className="text-xs text-gray-500">First Input Delay</div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <span>CLS</span>
            </div>
            <div className="text-lg font-semibold">{summary.cls}</div>
            <div className="text-xs text-gray-500">Cumulative Layout Shift</div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-purple-600" />
              <span>API</span>
            </div>
            <div className="text-lg font-semibold">{summary.apiResponseTime}</div>
            <div className="text-xs text-gray-500">API Response Time</div>
          </div>
        </div>

        {showDetails && (
          <>
            {/* Additional Metrics */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Additional Metrics</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Page Load:</span>
                  <span className="font-medium">{summary.pageLoadTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Memory:</span>
                  <span className="font-medium">
                    {metrics.memoryUsage ? `${metrics.memoryUsage.toFixed(1)}MB` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Clicks:</span>
                  <span className="font-medium">{metrics.clickCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Scroll Depth:</span>
                  <span className="font-medium">{metrics.scrollDepth}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Time on Page:</span>
                  <span className="font-medium">
                    {metrics.timeOnPage ? `${Math.round(metrics.timeOnPage / 1000)}s` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Errors:</span>
                  <span className="font-medium text-red-600">{metrics.errorCount}</span>
                </div>
              </div>
            </div>

            {/* Performance Recommendations */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Recommendations</h4>
              <div className="space-y-2 text-sm">
                {score < 70 && (
                  <div className="flex items-start gap-2 text-yellow-700">
                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>Consider optimizing page load performance</span>
                  </div>
                )}
                {parseFloat(summary.lcp.replace('ms', '')) > 2500 && (
                  <div className="flex items-start gap-2 text-orange-700">
                    <Zap className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>LCP is above recommended threshold (2.5s)</span>
                  </div>
                )}
                {parseFloat(summary.fid.replace('ms', '')) > 100 && (
                  <div className="flex items-start gap-2 text-orange-700">
                    <MousePointer className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>FID is above recommended threshold (100ms)</span>
                  </div>
                )}
                {parseFloat(summary.cls) > 0.1 && (
                  <div className="flex items-start gap-2 text-orange-700">
                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>CLS is above recommended threshold (0.1)</span>
                  </div>
                )}
                {metrics.errorCount > 0 && (
                  <div className="flex items-start gap-2 text-red-700">
                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>Consider investigating JavaScript errors</span>
                  </div>
                )}
                {score >= 90 && (
                  <div className="flex items-start gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>Excellent performance! Keep up the good work.</span>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
