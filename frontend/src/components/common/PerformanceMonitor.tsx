import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Zap, 
  Clock, 
  MemoryStick, 
  AlertTriangle,
  CheckCircle,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface PerformanceMetrics {
  lcp: number | null;
  fid: number | null;
  cls: number | null;
  fcp: number | null;
  ttfb: number | null;
  pageLoadTime: number | null;
  memoryUsage: number | null;
  performanceScore: number | null;
}

interface PerformanceMonitorProps {
  showDetails?: boolean;
  className?: string;
  onClose?: () => void;
}

export function PerformanceMonitor({ 
  showDetails = false, 
  className,
  onClose 
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    lcp: null,
    fid: null,
    cls: null,
    fcp: null,
    ttfb: null,
    pageLoadTime: null,
    memoryUsage: null,
    performanceScore: null,
  });
  const [isVisible, setIsVisible] = useState(showDetails);

  useEffect(() => {
    // Avoid installing timers in test environment to prevent open handles
    const isTest = typeof process !== 'undefined' && (process.env?.VITEST || process.env?.NODE_ENV === 'test');
    if (typeof window === 'undefined') return;

    // Get performance metrics
    const getPerformanceMetrics = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || null;
      const lcp = performance.getEntriesByType('largest-contentful-paint')[0]?.startTime || null;
      
      const pageLoadTime = navigation ? navigation.loadEventEnd - (navigation as any).navigationStart : null;
      const ttfb = navigation ? navigation.responseStart - navigation.requestStart : null;
      
      // Memory usage (if available)
      const memory = (performance as any).memory;
      const memoryUsage = memory ? memory.usedJSHeapSize / 1024 / 1024 : null; // Convert to MB
      
      // Calculate performance score
      let score = 100;
      if (lcp && lcp > 4000) score -= 30;
      else if (lcp && lcp > 2500) score -= 15;
      
      if (fcp && fcp > 3000) score -= 20;
      else if (fcp && fcp > 1500) score -= 10;
      
      if (pageLoadTime && pageLoadTime > 5000) score -= 25;
      else if (pageLoadTime && pageLoadTime > 3000) score -= 15;
      
      if (memoryUsage && memoryUsage > 100) score -= 15;
      else if (memoryUsage && memoryUsage > 50) score -= 10;

      setMetrics({
        lcp,
        fid: null, // FID requires user interaction
        cls: null, // CLS requires layout shift tracking
        fcp,
        ttfb,
        pageLoadTime,
        memoryUsage,
        performanceScore: Math.max(0, score),
      });
    };

    // Get metrics after page load
    if (document.readyState === 'complete') {
      getPerformanceMetrics();
    } else {
      window.addEventListener('load', getPerformanceMetrics);
    }

    // Update metrics periodically
    const interval = isTest ? undefined : setInterval(getPerformanceMetrics, 5000);

    return () => {
      window.removeEventListener('load', getPerformanceMetrics);
      if (interval) clearInterval(interval);
    };
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (score >= 70) return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    return <X className="h-4 w-4 text-red-500" />;
  };

  const formatValue = (value: number | null, unit: string = 'ms') => {
    if (value === null) return 'N/A';
    return `${Math.round(value)}${unit}`;
  };

  if (!isVisible) {
    return (
      <Button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 z-50"
        size="sm"
        variant="outline"
      >
        <Activity className="h-4 w-4 mr-2" />
        Performance
      </Button>
    );
  }

  return (
    <Card className={cn("fixed bottom-4 right-4 z-50 w-80 max-h-96 overflow-y-auto", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
            <CardTitle className="text-sm">Performance Monitor</CardTitle>
          </div>
          <Button
            onClick={() => {
              setIsVisible(false);
              onClose?.();
            }}
            size="sm"
            variant="ghost"
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription className="text-xs">
          Real-time performance metrics
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Performance Score */}
        <div className="space-y-2">
        <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Performance Score</span>
            <div className="flex items-center space-x-2">
              {getScoreIcon(metrics.performanceScore || 0)}
              <span className={cn("text-sm font-bold", getScoreColor(metrics.performanceScore || 0))}>
                {metrics.performanceScore || 0}
              </span>
            </div>
          </div>
          <Progress 
            value={metrics.performanceScore || 0} 
            className="h-2"
          />
        </div>

        {/* Core Web Vitals */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Core Web Vitals
          </h4>
          
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Zap className="h-3 w-3" />
                <span className="font-medium">LCP</span>
              </div>
              <div className="text-muted-foreground">
                {formatValue(metrics.lcp)}
            </div>
          </div>
          
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span className="font-medium">FCP</span>
            </div>
              <div className="text-muted-foreground">
                {formatValue(metrics.fcp)}
            </div>
          </div>
          
            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <Activity className="h-3 w-3" />
                <span className="font-medium">TTFB</span>
            </div>
              <div className="text-muted-foreground">
                {formatValue(metrics.ttfb)}
          </div>
        </div>

            <div className="space-y-1">
              <div className="flex items-center space-x-1">
                <MemoryStick className="h-3 w-3" />
                <span className="font-medium">Memory</span>
                </div>
              <div className="text-muted-foreground">
                {formatValue(metrics.memoryUsage, 'MB')}
                </div>
                </div>
              </div>
            </div>

        {/* Page Load Time */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium">Page Load Time</span>
            <span className="text-xs text-muted-foreground">
              {formatValue(metrics.pageLoadTime)}
            </span>
                  </div>
                  </div>

        {/* Performance Tips */}
        {metrics.performanceScore && metrics.performanceScore < 70 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Optimization Tips
            </h4>
            <div className="space-y-1 text-xs text-muted-foreground">
              {metrics.lcp && metrics.lcp > 2500 && (
                <div>• Optimize images and reduce LCP</div>
              )}
              {metrics.fcp && metrics.fcp > 1500 && (
                <div>• Minimize render-blocking resources</div>
              )}
              {metrics.memoryUsage && metrics.memoryUsage > 50 && (
                <div>• Reduce memory usage</div>
              )}
              {metrics.pageLoadTime && metrics.pageLoadTime > 3000 && (
                <div>• Optimize bundle size</div>
                )}
              </div>
            </div>
        )}
      </CardContent>
    </Card>
  );
}
