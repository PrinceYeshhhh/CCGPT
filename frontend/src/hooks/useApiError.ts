import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
  field?: string;
}

export interface ApiErrorState {
  error: ApiError | null;
  isLoading: boolean;
  isRetrying: boolean;
}

export function useApiError() {
  const [state, setState] = useState<ApiErrorState>({
    error: null,
    isLoading: false,
    isRetrying: false,
  });

  const handleError = useCallback((error: any, options?: {
    showToast?: boolean;
    fallbackMessage?: string;
    onError?: (error: ApiError) => void;
  }) => {
    const {
      showToast = true,
      fallbackMessage = 'An unexpected error occurred',
      onError
    } = options || {};

    let apiError: ApiError;

    if (error?.response) {
      // Server responded with error status
      const { status, data } = error.response;
      apiError = {
        message: data?.message || data?.detail || data?.error || fallbackMessage,
        status,
        code: data?.code,
        details: data?.details,
        field: data?.field,
      };
    } else if (error?.request) {
      // Network error
      apiError = {
        message: 'Network error. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
      };
    } else {
      // Other error
      apiError = {
        message: error?.message || fallbackMessage,
        code: 'UNKNOWN_ERROR',
      };
    }

    setState(prev => ({
      ...prev,
      error: apiError,
      isLoading: false,
      isRetrying: false,
    }));

    if (showToast) {
      toast.error(apiError.message);
    }

    if (onError) {
      onError(apiError);
    }

    return apiError;
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({
      ...prev,
      isLoading: loading,
    }));
  }, []);

  const setRetrying = useCallback((retrying: boolean) => {
    setState(prev => ({
      ...prev,
      isRetrying: retrying,
    }));
  }, []);

  const retry = useCallback(async (retryFn: () => Promise<any>, options?: {
    showToast?: boolean;
    onSuccess?: () => void;
    onError?: (error: ApiError) => void;
  }) => {
    const {
      showToast = true,
      onSuccess,
      onError
    } = options || {};

    try {
      setRetrying(true);
      clearError();
      
      const result = await retryFn();
      
      setState(prev => ({
        ...prev,
        error: null,
        isLoading: false,
        isRetrying: false,
      }));

      if (showToast) {
        toast.success('Operation completed successfully');
      }

      if (onSuccess) {
        onSuccess();
      }

      return result;
    } catch (error) {
      return handleError(error, { showToast, onError });
    } finally {
      setRetrying(false);
    }
  }, [handleError, clearError, setRetrying]);

  const executeWithErrorHandling = useCallback(async <T>(
    apiCall: () => Promise<T>,
    options?: {
      showToast?: boolean;
      onSuccess?: (result: T) => void;
      onError?: (error: ApiError) => void;
      loadingMessage?: string;
    }
  ): Promise<T | null> => {
    const {
      showToast = true,
      onSuccess,
      onError,
      loadingMessage
    } = options || {};

    try {
      setLoading(true);
      clearError();

      if (loadingMessage && showToast) {
        toast.loading(loadingMessage);
      }

      const result = await apiCall();
      
      setState(prev => ({
        ...prev,
        error: null,
        isLoading: false,
      }));

      if (showToast && loadingMessage) {
        toast.dismiss();
        toast.success('Operation completed successfully');
      }

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (error) {
      const apiError = handleError(error, { showToast, onError });
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError, clearError, setLoading]);

  return {
    ...state,
    handleError,
    clearError,
    setLoading,
    setRetrying,
    retry,
    executeWithErrorHandling,
  };
}

// Error message formatters
export const formatApiError = (error: ApiError): string => {
  if (error.field) {
    return `${error.field}: ${error.message}`;
  }
  return error.message;
};

export const getErrorSeverity = (error: ApiError): 'low' | 'medium' | 'high' => {
  if (error.status) {
    if (error.status >= 500) return 'high';
    if (error.status >= 400) return 'medium';
    return 'low';
  }
  return 'medium';
};

export const isRetryableError = (error: ApiError): boolean => {
  if (error.status) {
    // Retry on server errors and some client errors
    return error.status >= 500 || error.status === 408 || error.status === 429;
  }
  // Retry on network errors
  return error.code === 'NETWORK_ERROR';
};

// Common error messages
export const commonErrorMessages = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied. You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
  TIMEOUT: 'Request timed out. Please try again.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
};
