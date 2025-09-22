import { useEffect, useCallback, useRef, useState } from 'react'

interface PerformanceMetrics {
  loadTime: number
  renderTime: number
  memoryUsage?: number
  networkLatency?: number
}

export const usePerformance = () => {
  const startTime = useRef<number>(Date.now())
  const renderStartTime = useRef<number>(0)

  const measureRenderTime = useCallback((componentName: string) => {
    const renderTime = Date.now() - renderStartTime.current
    console.log(`${componentName} render time: ${renderTime}ms`)
    
    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', 'timing_complete', {
        name: componentName,
        value: renderTime
      })
    }
  }, [])

  const measureLoadTime = useCallback((componentName: string) => {
    const loadTime = Date.now() - startTime.current
    console.log(`${componentName} load time: ${loadTime}ms`)
    
    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', 'timing_complete', {
        name: `${componentName}_load`,
        value: loadTime
      })
    }
  }, [])

  const measureMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const memoryUsage = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      }
      
      console.log('Memory usage:', memoryUsage)
      return memoryUsage
    }
    return null
  }, [])

  const measureNetworkLatency = useCallback(async (url: string) => {
    const start = performance.now()
    try {
      await fetch(url, { method: 'HEAD' })
      const latency = performance.now() - start
      console.log(`Network latency to ${url}: ${latency}ms`)
      return latency
    } catch (error) {
      console.error('Network latency measurement failed:', error)
      return null
    }
  }, [])

  const startRenderMeasurement = useCallback(() => {
    renderStartTime.current = Date.now()
  }, [])

  const endRenderMeasurement = useCallback((componentName: string) => {
    measureRenderTime(componentName)
  }, [measureRenderTime])

  // Performance observer for long tasks
  useEffect(() => {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 50) { // Tasks longer than 50ms
            console.warn('Long task detected:', {
              name: entry.name,
              duration: entry.duration,
              startTime: entry.startTime
            })
            
            // Send to analytics
            if (window.gtag) {
              window.gtag('event', 'long_task', {
                duration: Math.round(entry.duration),
                name: entry.name
              })
            }
          }
        }
      })
      
      observer.observe({ entryTypes: ['longtask'] })
      
      return () => observer.disconnect()
    }
  }, [])

  // Memory usage monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      const memory = measureMemoryUsage()
      if (memory && memory.used / memory.limit > 0.8) {
        console.warn('High memory usage detected:', memory)
      }
    }, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [measureMemoryUsage])

  return {
    measureRenderTime,
    measureLoadTime,
    measureMemoryUsage,
    measureNetworkLatency,
    startRenderMeasurement,
    endRenderMeasurement
  }
}

// Hook for lazy loading components
export const useLazyLoad = (threshold = 0.1) => {
  const [isVisible, setIsVisible] = useState(false)
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { threshold }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [threshold])

  return [ref, isVisible] as const
}

// Hook for debouncing expensive operations
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Hook for throttling function calls
export const useThrottle = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T => {
  const lastCall = useRef<number>(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now()
      
      if (now - lastCall.current >= delay) {
        lastCall.current = now
        return func(...args)
      } else {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = setTimeout(() => {
          lastCall.current = Date.now()
          func(...args)
        }, delay - (now - lastCall.current))
      }
    }) as T,
    [func, delay]
  )
}
