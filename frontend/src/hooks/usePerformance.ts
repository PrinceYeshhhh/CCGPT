import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';

export interface PerformanceMetrics {
  // Core Web Vitals
  lcp: number | null; // Largest Contentful Paint
  fid: number | null; // First Input Delay
  cls: number | null; // Cumulative Layout Shift
  fcp: number | null; // First Contentful Paint
  ttfb: number | null; // Time to First Byte
  
  // Custom metrics
  pageLoadTime: number | null;
  apiResponseTime: number | null;
  renderTime: number | null;
  memoryUsage: number | null;
  
  // User interaction metrics
  clickCount: number;
  scrollDepth: number;
  timeOnPage: number;
  
  // Error metrics
  errorCount: number;
  apiErrorCount: number;
  
  // Performance scores
  performanceScore: number | null;
  accessibilityScore: number | null;
  bestPracticesScore: number | null;
  seoScore: number | null;
}

export interface PerformanceConfig {
  enableWebVitals: boolean;
  enableCustomMetrics: boolean;
  enableUserTracking: boolean;
  enableErrorTracking: boolean;
  enableLighthouse: boolean;
  reportInterval: number; // milliseconds
  batchSize: number;
}

const defaultConfig: PerformanceConfig = {
  enableWebVitals: true,
  enableCustomMetrics: true,
  enableUserTracking: true,
  enableErrorTracking: true,
  enableLighthouse: false,
  reportInterval: 30000, // 30 seconds
  batchSize: 10,
};

export function usePerformance(config: Partial<PerformanceConfig> = {}) {
  const finalConfig = { ...defaultConfig, ...config };
  
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    lcp: null,
    fid: null,
    cls: null,
    fcp: null,
    ttfb: null,
    pageLoadTime: null,
    apiResponseTime: null,
    renderTime: null,
    memoryUsage: null,
    clickCount: 0,
    scrollDepth: 0,
    timeOnPage: 0,
    errorCount: 0,
    apiErrorCount: 0,
    performanceScore: null,
    accessibilityScore: null,
    bestPracticesScore: null,
    seoScore: null,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const startTime = useRef<number>(Date.now());
  const pageStartTime = useRef<number>(performance.now());
  const metricsBuffer = useRef<PerformanceMetrics[]>([]);
  const observerRef = useRef<PerformanceObserver | null>(null);
  const reportIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize performance monitoring
  useEffect(() => {
    if (finalConfig.enableWebVitals) {
      initializeWebVitals();
    }
    
    if (finalConfig.enableCustomMetrics) {
      initializeCustomMetrics();
    }
    
    if (finalConfig.enableUserTracking) {
      initializeUserTracking();
    }
    
    if (finalConfig.enableErrorTracking) {
      initializeErrorTracking();
    }

    // Set up periodic reporting
    if (finalConfig.reportInterval > 0) {
      reportIntervalRef.current = setInterval(reportMetrics, finalConfig.reportInterval);
    }

    return () => {
      cleanup();
    };
  }, [finalConfig]);

  // Web Vitals monitoring
  const initializeWebVitals = useCallback(() => {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    try {
      // LCP - Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as PerformanceEntry;
        setMetrics(prev => ({ ...prev, lcp: lastEntry.startTime }));
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

      // FID - First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          setMetrics(prev => ({ ...prev, fid: entry.processingStart - entry.startTime }));
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });

      // CLS - Cumulative Layout Shift
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            setMetrics(prev => ({ ...prev, cls: clsValue }));
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });

      // FCP - First Contentful Paint
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name === 'first-contentful-paint') {
            setMetrics(prev => ({ ...prev, fcp: entry.startTime }));
          }
        });
      });
      fcpObserver.observe({ entryTypes: ['paint'] });

      // TTFB - Time to First Byte
      const ttfbObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            setMetrics(prev => ({ 
              ...prev, 
              ttfb: navEntry.responseStart - navEntry.requestStart 
            }));
          }
        });
      });
      ttfbObserver.observe({ entryTypes: ['navigation'] });

    } catch (error) {
      console.warn('Failed to initialize Web Vitals:', error);
    }
  }, []);

  // Custom metrics monitoring
  const initializeCustomMetrics = useCallback(() => {
    // Page load time
    const pageLoadTime = performance.now() - pageStartTime.current;
    setMetrics(prev => ({ ...prev, pageLoadTime }));

    // Memory usage (if available)
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      setMetrics(prev => ({ 
        ...prev, 
        memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // Convert to MB
      }));
    }

    // Render time measurement
    const renderStart = performance.now();
    requestAnimationFrame(() => {
      const renderTime = performance.now() - renderStart;
      setMetrics(prev => ({ ...prev, renderTime }));
    });
  }, []);

  // User interaction tracking
  const initializeUserTracking = useCallback(() => {
    let clickCount = 0;
    let maxScrollDepth = 0;

    const handleClick = () => {
      clickCount++;
      setMetrics(prev => ({ ...prev, clickCount }));
    };

    const handleScroll = () => {
      const scrollDepth = Math.round(
        (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100
      );
      maxScrollDepth = Math.max(maxScrollDepth, scrollDepth);
      setMetrics(prev => ({ ...prev, scrollDepth: maxScrollDepth }));
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        const timeOnPage = Date.now() - startTime.current;
        setMetrics(prev => ({ ...prev, timeOnPage }));
      }
    };

    document.addEventListener('click', handleClick);
    document.addEventListener('scroll', handleScroll);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('scroll', handleScroll);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Error tracking
  const initializeErrorTracking = useCallback(() => {
    let errorCount = 0;
    let apiErrorCount = 0;

    const handleError = (event: ErrorEvent) => {
      errorCount++;
      setMetrics(prev => ({ ...prev, errorCount }));
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      errorCount++;
      setMetrics(prev => ({ ...prev, errorCount }));
    };

    // Track API errors via axios interceptor
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        apiErrorCount++;
        setMetrics(prev => ({ ...prev, apiErrorCount }));
        return Promise.reject(error);
      }
    );

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  // Track API response time
  const trackApiCall = useCallback(async <T>(apiCall: () => Promise<T>): Promise<T> => {
    const startTime = performance.now();
    try {
      const result = await apiCall();
      const responseTime = performance.now() - startTime;
      setMetrics(prev => ({ ...prev, apiResponseTime: responseTime }));
      return result;
    } catch (error) {
      const responseTime = performance.now() - startTime;
      setMetrics(prev => ({ 
        ...prev, 
        apiResponseTime: responseTime,
        apiErrorCount: prev.apiErrorCount + 1
      }));
      throw error;
    }
  }, []);

  // Report metrics to backend
  const reportMetrics = useCallback(async () => {
    if (metricsBuffer.current.length === 0) return;

    try {
      setIsLoading(true);
      setError(null);

      await api.post('/analytics/performance', {
        metrics: metricsBuffer.current,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      });

      metricsBuffer.current = [];
    } catch (err) {
      console.error('Failed to report performance metrics:', err);
      setError('Failed to report metrics');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Add metrics to buffer
  const addMetrics = useCallback((newMetrics: Partial<PerformanceMetrics>) => {
    const updatedMetrics = { ...metrics, ...newMetrics };
    setMetrics(updatedMetrics);
    
    metricsBuffer.current.push(updatedMetrics);
    
    // Report if buffer is full
    if (metricsBuffer.current.length >= finalConfig.batchSize) {
      reportMetrics();
    }
  }, [metrics, finalConfig.batchSize, reportMetrics]);

  // Get performance score
  const getPerformanceScore = useCallback(() => {
    const { lcp, fid, cls, fcp, ttfb } = metrics;
    
    let score = 100;
    
    // LCP scoring (0-2.5s = 100, 2.5-4s = 50, >4s = 0)
    if (lcp !== null) {
      if (lcp > 4000) score -= 50;
      else if (lcp > 2500) score -= 25;
    }
    
    // FID scoring (0-100ms = 100, 100-300ms = 50, >300ms = 0)
    if (fid !== null) {
      if (fid > 300) score -= 50;
      else if (fid > 100) score -= 25;
    }
    
    // CLS scoring (0-0.1 = 100, 0.1-0.25 = 50, >0.25 = 0)
    if (cls !== null) {
      if (cls > 0.25) score -= 50;
      else if (cls > 0.1) score -= 25;
    }
    
    return Math.max(0, score);
  }, [metrics]);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (reportIntervalRef.current) {
      clearInterval(reportIntervalRef.current);
    }
    if (observerRef.current) {
      observerRef.current.disconnect();
    }
  }, []);

  // Get current performance summary
  const getPerformanceSummary = useCallback(() => {
    const score = getPerformanceScore();
    const { lcp, fid, cls, pageLoadTime, apiResponseTime, errorCount } = metrics;
    
    return {
      score,
      lcp: lcp ? `${lcp.toFixed(0)}ms` : 'N/A',
      fid: fid ? `${fid.toFixed(0)}ms` : 'N/A',
      cls: cls ? cls.toFixed(3) : 'N/A',
      pageLoadTime: pageLoadTime ? `${pageLoadTime.toFixed(0)}ms` : 'N/A',
      apiResponseTime: apiResponseTime ? `${apiResponseTime.toFixed(0)}ms` : 'N/A',
      errorCount,
    };
  }, [metrics, getPerformanceScore]);

  return {
    metrics,
    isLoading,
    error,
    trackApiCall,
    addMetrics,
    reportMetrics,
    getPerformanceScore,
    getPerformanceSummary,
  };
}
