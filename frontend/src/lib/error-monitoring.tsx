import React from 'react'
import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/tracing'

// Initialize Sentry
export function initErrorMonitoring() {
  if (typeof window === 'undefined') return

  const dsn = import.meta.env.VITE_SENTRY_DSN
  const environment = import.meta.env.MODE
  const release = import.meta.env.VITE_APP_VERSION || '1.0.0'

  if (!dsn) {
    // eslint-disable-next-line no-console
    console.warn('Sentry DSN not provided. Error monitoring disabled.')
    return
  }

  Sentry.init({
    dsn,
    environment,
    release,
    integrations: [
      new BrowserTracing({
        tracingOrigins: ['localhost', '127.0.0.1', /^https:\/\/customercaregpt/],
        // Router instrumentation can be added later when needed
      }),
    ],
    tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
    sampleRate: 1.0,
    beforeSend(event) {
      if (environment === 'development' && event.level !== 'error') {
        return null
      }
      event.tags = {
        ...event.tags,
        component: 'frontend',
        version: release,
      }
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user?.id) {
          event.user = {
            id: user.id,
            username: user.username,
            email: user.email,
          }
        }
      } catch {}
      return event
    },
    beforeBreadcrumb(breadcrumb) {
      if (breadcrumb.category === 'http' && breadcrumb.data) {
        const sensitiveKeys = ['password', 'token', 'authorization', 'cookie']
        for (const key of sensitiveKeys) {
          if (breadcrumb.data?.[key]) breadcrumb.data[key] = '[Filtered]'
        }
      }
      return breadcrumb
    },
  })
}

// Use Sentry's ErrorBoundary component for JSX usage
export const ErrorBoundary = Sentry.ErrorBoundary

export const performanceMonitoring = {
  trackCustomMetric: (name: string, value: number, tags?: Record<string, string>) => {
    Sentry.addBreadcrumb({ message: `Custom metric: ${name}`, level: 'info', data: { value, ...tags } })
  },
  trackApiCall: (url: string, method: string, duration: number, status: number) => {
    Sentry.addBreadcrumb({ message: `API Call: ${method} ${url}`, level: status >= 400 ? 'error' : 'info', data: { url, method, duration, status } })
  },
  trackUserAction: (action: string, component: string, data?: Record<string, any>) => {
    Sentry.addBreadcrumb({ message: `User Action: ${action}`, level: 'info', data: { action, component, ...data } })
  },
  trackPageView: (pathname: string, search?: string) => {
    Sentry.addBreadcrumb({ message: `Page View: ${pathname}`, level: 'info', data: { pathname, search } })
  },
}

export const errorReporting = {
  reportError: (error: Error, context?: Record<string, any>) => {
    Sentry.captureException(error, { tags: context })
  },
  reportApiError: (url: string, method: string, error: Error, status?: number) => {
    Sentry.captureException(error, { tags: { type: 'api_error', url, method, status: status?.toString() } })
  },
  reportUserFeedback: (feedback: string, email?: string) => {
    Sentry.captureUserFeedback({ event_id: Sentry.captureMessage('User Feedback'), name: email || 'Anonymous', email: email || '', comments: feedback })
  },
  setUser: (user: { id: string; username?: string; email?: string }) => {
    Sentry.setUser(user)
  },
  clearUser: () => {
    Sentry.setUser(null)
  },
  setContext: (key: string, context: any) => {
    Sentry.setContext(key, context)
  },
  setTags: (tags: Record<string, string>) => {
    Sentry.setTags(tags)
  },
}

export function ErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 className="text-lg font-medium text-foreground mb-2">Something went wrong</h1>
          <p className="text-sm text-muted-foreground mb-4">We're sorry, but something unexpected happened. Our team has been notified.</p>
          <div className="space-y-2">
            <button onClick={resetError} className="w-full bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90">Try again</button>
            <button onClick={() => (window.location.href = '/')} className="w-full bg-secondary text-secondary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-secondary/90">Go home</button>
          </div>
        </div>
      </div>
    </div>
  )
}
