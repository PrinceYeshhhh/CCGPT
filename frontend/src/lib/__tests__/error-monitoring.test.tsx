import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { initErrorMonitoring, performanceMonitoring, errorReporting, ErrorFallback } from '../error-monitoring';

// Mock Sentry
vi.mock('@sentry/react', () => ({
  init: vi.fn(),
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div data-testid="sentry-error-boundary">{children}</div>,
  addBreadcrumb: vi.fn(),
  captureException: vi.fn(),
  captureMessage: vi.fn(),
  captureUserFeedback: vi.fn(),
  setUser: vi.fn(),
  setContext: vi.fn(),
  setTags: vi.fn(),
}));

vi.mock('@sentry/tracing', () => ({
  BrowserTracing: vi.fn().mockImplementation(() => ({})),
}));

// Mock environment variables
const originalEnv = import.meta.env;

describe('error-monitoring', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
    });
  });

  afterEach(() => {
    Object.defineProperty(import.meta, 'env', {
      value: originalEnv,
      writable: true,
    });
  });

  describe('initErrorMonitoring', () => {
    it('should not initialize when window is undefined', () => {
      const originalWindow = global.window;
      // @ts-ignore
      delete global.window;
      
      initErrorMonitoring();
      
      // @ts-ignore
      global.window = originalWindow;
    });

    it('should warn when DSN is not provided', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      Object.defineProperty(import.meta, 'env', {
        value: { ...originalEnv, VITE_SENTRY_DSN: undefined },
        writable: true,
      });
      
      initErrorMonitoring();
      
      expect(consoleSpy).toHaveBeenCalledWith('Sentry DSN not provided. Error monitoring disabled.');
      consoleSpy.mockRestore();
    });

    it('should initialize Sentry with correct configuration', () => {
      const { init } = require('@sentry/react');
      
      Object.defineProperty(import.meta, 'env', {
        value: { 
          ...originalEnv, 
          VITE_SENTRY_DSN: 'https://test@sentry.io/test',
          MODE: 'production',
          VITE_APP_VERSION: '1.2.3',
        },
        writable: true,
      });
      
      initErrorMonitoring();
      
      expect(init).toHaveBeenCalledWith({
        dsn: 'https://test@sentry.io/test',
        environment: 'production',
        release: '1.2.3',
        integrations: expect.any(Array),
        tracesSampleRate: 0.1,
        sampleRate: 1.0,
        beforeSend: expect.any(Function),
        beforeBreadcrumb: expect.any(Function),
      });
    });

    it('should set correct trace sample rate for development', () => {
      const { init } = require('@sentry/react');
      
      Object.defineProperty(import.meta, 'env', {
        value: { 
          ...originalEnv, 
          VITE_SENTRY_DSN: 'https://test@sentry.io/test',
          MODE: 'development',
        },
        writable: true,
      });
      
      initErrorMonitoring();
      
      expect(init).toHaveBeenCalledWith(
        expect.objectContaining({
          tracesSampleRate: 1.0,
        })
      );
    });
  });

  describe('performanceMonitoring', () => {
    it('should track custom metric', () => {
      const { addBreadcrumb } = require('@sentry/react');
      
      performanceMonitoring.trackCustomMetric('test-metric', 123, { tag: 'value' });
      
      expect(addBreadcrumb).toHaveBeenCalledWith({
        message: 'Custom metric: test-metric',
        level: 'info',
        data: { value: 123, tag: 'value' },
      });
    });

    it('should track API call', () => {
      const { addBreadcrumb } = require('@sentry/react');
      
      performanceMonitoring.trackApiCall('/api/test', 'POST', 150, 200);
      
      expect(addBreadcrumb).toHaveBeenCalledWith({
        message: 'API Call: POST /api/test',
        level: 'info',
        data: { url: '/api/test', method: 'POST', duration: 150, status: 200 },
      });
    });

    it('should track API call error', () => {
      const { addBreadcrumb } = require('@sentry/react');
      
      performanceMonitoring.trackApiCall('/api/test', 'POST', 150, 500);
      
      expect(addBreadcrumb).toHaveBeenCalledWith({
        message: 'API Call: POST /api/test',
        level: 'error',
        data: { url: '/api/test', method: 'POST', duration: 150, status: 500 },
      });
    });

    it('should track user action', () => {
      const { addBreadcrumb } = require('@sentry/react');
      
      performanceMonitoring.trackUserAction('click', 'button', { id: 'test-btn' });
      
      expect(addBreadcrumb).toHaveBeenCalledWith({
        message: 'User Action: click',
        level: 'info',
        data: { action: 'click', component: 'button', id: 'test-btn' },
      });
    });

    it('should track page view', () => {
      const { addBreadcrumb } = require('@sentry/react');
      
      performanceMonitoring.trackPageView('/dashboard', '?tab=settings');
      
      expect(addBreadcrumb).toHaveBeenCalledWith({
        message: 'Page View: /dashboard',
        level: 'info',
        data: { pathname: '/dashboard', search: '?tab=settings' },
      });
    });
  });

  describe('errorReporting', () => {
    it('should report error', () => {
      const { captureException } = require('@sentry/react');
      const error = new Error('Test error');
      const context = { component: 'test' };
      
      errorReporting.reportError(error, context);
      
      expect(captureException).toHaveBeenCalledWith(error, { tags: context });
    });

    it('should report API error', () => {
      const { captureException } = require('@sentry/react');
      const error = new Error('API error');
      
      errorReporting.reportApiError('/api/test', 'POST', error, 500);
      
      expect(captureException).toHaveBeenCalledWith(error, {
        tags: { type: 'api_error', url: '/api/test', method: 'POST', status: '500' },
      });
    });

    it('should report user feedback', () => {
      const { captureMessage, captureUserFeedback } = require('@sentry/react');
      const eventId = 'test-event-id';
      
      captureMessage.mockReturnValue(eventId);
      
      errorReporting.reportUserFeedback('Great app!', 'user@example.com');
      
      expect(captureMessage).toHaveBeenCalledWith('User Feedback');
      expect(captureUserFeedback).toHaveBeenCalledWith({
        event_id: eventId,
        name: 'user@example.com',
        email: 'user@example.com',
        comments: 'Great app!',
      });
    });

    it('should report user feedback without email', () => {
      const { captureMessage, captureUserFeedback } = require('@sentry/react');
      const eventId = 'test-event-id';
      
      captureMessage.mockReturnValue(eventId);
      
      errorReporting.reportUserFeedback('Great app!');
      
      expect(captureUserFeedback).toHaveBeenCalledWith({
        event_id: eventId,
        name: 'Anonymous',
        email: '',
        comments: 'Great app!',
      });
    });

    it('should set user', () => {
      const { setUser } = require('@sentry/react');
      const user = { id: '123', username: 'test', email: 'test@example.com' };
      
      errorReporting.setUser(user);
      
      expect(setUser).toHaveBeenCalledWith(user);
    });

    it('should clear user', () => {
      const { setUser } = require('@sentry/react');
      
      errorReporting.clearUser();
      
      expect(setUser).toHaveBeenCalledWith(null);
    });

    it('should set context', () => {
      const { setContext } = require('@sentry/react');
      const context = { key: 'value' };
      
      errorReporting.setContext('test', context);
      
      expect(setContext).toHaveBeenCalledWith('test', context);
    });

    it('should set tags', () => {
      const { setTags } = require('@sentry/react');
      const tags = { environment: 'test', version: '1.0.0' };
      
      errorReporting.setTags(tags);
      
      expect(setTags).toHaveBeenCalledWith(tags);
    });
  });

  describe('ErrorFallback', () => {
    it('should render error fallback UI', () => {
      const mockResetError = vi.fn();
      const error = new Error('Test error');
      
      render(<ErrorFallback error={error} resetError={mockResetError} />);
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText("We're sorry, but something unexpected happened. Our team has been notified.")).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();
      expect(screen.getByText('Go home')).toBeInTheDocument();
    });

    it('should call resetError when Try again is clicked', () => {
      const mockResetError = vi.fn();
      const error = new Error('Test error');
      
      render(<ErrorFallback error={error} resetError={mockResetError} />);
      
      fireEvent.click(screen.getByText('Try again'));
      
      expect(mockResetError).toHaveBeenCalledTimes(1);
    });

    it('should navigate to home when Go home is clicked', () => {
      const mockResetError = vi.fn();
      const error = new Error('Test error');
      
      // Mock window.location.href
      delete (window as any).location;
      window.location = { href: '' } as any;
      
      render(<ErrorFallback error={error} resetError={mockResetError} />);
      
      fireEvent.click(screen.getByText('Go home'));
      
      expect(window.location.href).toBe('/');
    });

    it('should have proper styling classes', () => {
      const mockResetError = vi.fn();
      const error = new Error('Test error');
      
      render(<ErrorFallback error={error} resetError={mockResetError} />);
      
      const container = screen.getByText('Something went wrong').closest('div');
      expect(container).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center', 'bg-background');
    });
  });
});
