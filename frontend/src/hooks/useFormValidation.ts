import { useState, useCallback } from 'react';
import { FieldError } from 'react-hook-form';

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

export interface ValidationRules {
  [key: string]: ValidationRule;
}

export interface ValidationState {
  errors: Record<string, string>;
  isValid: boolean;
  isDirty: boolean;
  touched: Record<string, boolean>;
}

export function useFormValidation(rules: ValidationRules) {
  const [state, setState] = useState<ValidationState>({
    errors: {},
    isValid: true,
    isDirty: false,
    touched: {},
  });

  const validateField = useCallback((name: string, value: any): string | null => {
    const rule = rules[name];
    if (!rule) return null;

    // Required validation
    if (rule.required && (!value || value.toString().trim() === '')) {
      return `${name} is required`;
    }

    // Skip other validations if value is empty and not required
    if (!value || value.toString().trim() === '') {
      return null;
    }

    // Min length validation
    if (rule.minLength && value.toString().length < rule.minLength) {
      return `${name} must be at least ${rule.minLength} characters`;
    }

    // Max length validation
    if (rule.maxLength && value.toString().length > rule.maxLength) {
      return `${name} must be no more than ${rule.maxLength} characters`;
    }

    // Pattern validation
    if (rule.pattern && !rule.pattern.test(value.toString())) {
      return `${name} format is invalid`;
    }

    // Custom validation
    if (rule.custom) {
      return rule.custom(value);
    }

    return null;
  }, [rules]);

  const validateForm = useCallback((values: Record<string, any>): boolean => {
    const errors: Record<string, string> = {};
    let isValid = true;

    Object.keys(rules).forEach(fieldName => {
      const error = validateField(fieldName, values[fieldName]);
      if (error) {
        errors[fieldName] = error;
        isValid = false;
      }
    });

    setState(prev => ({
      ...prev,
      errors,
      isValid,
    }));

    return isValid;
  }, [rules, validateField]);

  const setFieldValue = useCallback((name: string, value: any) => {
    const error = validateField(name, value);
    
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [name]: error || '',
      },
      isDirty: true,
      touched: {
        ...prev.touched,
        [name]: true,
      },
    }));
  }, [validateField]);

  const setFieldTouched = useCallback((name: string) => {
    setState(prev => ({
      ...prev,
      touched: {
        ...prev.touched,
        [name]: true,
      },
    }));
  }, []);

  const clearErrors = useCallback(() => {
    setState(prev => ({
      ...prev,
      errors: {},
      isValid: true,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      errors: {},
      isValid: true,
      isDirty: false,
      touched: {},
    });
  }, []);

  const getFieldError = useCallback((name: string): string | null => {
    return state.errors[name] || null;
  }, [state.errors]);

  const isFieldTouched = useCallback((name: string): boolean => {
    return state.touched[name] || false;
  }, [state.touched]);

  const hasFieldError = useCallback((name: string): boolean => {
    return !!state.errors[name];
  }, [state.errors]);

  return {
    ...state,
    validateField,
    validateForm,
    setFieldValue,
    setFieldTouched,
    clearErrors,
    reset,
    getFieldError,
    isFieldTouched,
    hasFieldError,
  };
}

// Common validation rules
export const commonValidationRules = {
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  password: {
    required: true,
    minLength: 8,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
  },
  phone: {
    required: true,
    pattern: /^\+?[\d\s-()]+$/,
    minLength: 10,
  },
  username: {
    required: true,
    minLength: 3,
    maxLength: 20,
    pattern: /^[a-zA-Z0-9_]+$/,
  },
  required: {
    required: true,
  },
  optional: {},
};

// Validation helpers
export const validateEmail = (email: string): string | null => {
  if (!email) return 'Email is required';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return 'Please enter a valid email address';
  }
  return null;
};

export const validatePassword = (password: string): string | null => {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';
  if (!/(?=.*[a-z])/.test(password)) return 'Password must contain at least one lowercase letter';
  if (!/(?=.*[A-Z])/.test(password)) return 'Password must contain at least one uppercase letter';
  if (!/(?=.*\d)/.test(password)) return 'Password must contain at least one number';
  return null;
};

export const validatePhone = (phone: string): string | null => {
  if (!phone) return 'Phone number is required';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length < 10) return 'Phone number must be at least 10 digits';
  if (cleaned.length > 15) return 'Phone number must be no more than 15 digits';
  return null;
};

export const validateUsername = (username: string): string | null => {
  if (!username) return 'Username is required';
  if (username.length < 3) return 'Username must be at least 3 characters';
  if (username.length > 20) return 'Username must be no more than 20 characters';
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return 'Username can only contain letters, numbers, and underscores';
  }
  return null;
};

export const validateConfirmPassword = (password: string, confirmPassword: string): string | null => {
  if (!confirmPassword) return 'Please confirm your password';
  if (password !== confirmPassword) return 'Passwords do not match';
  return null;
};
