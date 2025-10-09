import { describe, it, expect } from 'vitest';
import { cn, formatDate, formatCurrency } from '../utils';

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2');
    });

    it('should handle conditional classes', () => {
      expect(cn('base', true && 'conditional', false && 'hidden')).toBe('base conditional');
    });

    it('should handle arrays of classes', () => {
      expect(cn(['class1', 'class2'], 'class3')).toBe('class1 class2 class3');
    });

    it('should handle objects with boolean values', () => {
      expect(cn({ 'class1': true, 'class2': false, 'class3': true })).toBe('class1 class3');
    });

    it('should handle mixed inputs', () => {
      expect(cn('base', { 'conditional': true }, ['array1', 'array2'], false && 'hidden')).toBe('base conditional array1 array2');
    });

    it('should handle empty inputs', () => {
      expect(cn()).toBe('');
      expect(cn('')).toBe('');
      expect(cn(null, undefined, false)).toBe('');
    });

    it('should merge conflicting Tailwind classes', () => {
      // This tests the twMerge functionality
      expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    });
  });

  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2023-12-25T10:30:00Z');
      const formatted = formatDate(date);
      expect(formatted).toBe('Dec 25, 2023');
    });

    it('should handle different dates', () => {
      const date1 = new Date('2024-01-01T00:00:00Z');
      expect(formatDate(date1)).toBe('Jan 1, 2024');

      const date2 = new Date('2023-06-15T12:00:00Z');
      expect(formatDate(date2)).toBe('Jun 15, 2023');
    });

    it('should handle edge cases', () => {
      const date = new Date('2000-02-29T00:00:00Z'); // Leap year
      expect(formatDate(date)).toBe('Feb 29, 2000');
    });
  });

  describe('formatCurrency', () => {
    it('should format currency correctly', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(0)).toBe('$0.00');
      expect(formatCurrency(100)).toBe('$100.00');
    });

    it('should handle negative amounts', () => {
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
    });

    it('should handle large amounts', () => {
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
    });

    it('it should handle decimal precision', () => {
      expect(formatCurrency(1234.1)).toBe('$1,234.10');
      expect(formatCurrency(1234.123)).toBe('$1,234.12'); // Rounds to 2 decimal places
    });

    it('should handle very small amounts', () => {
      expect(formatCurrency(0.01)).toBe('$0.01');
      expect(formatCurrency(0.1)).toBe('$0.10');
    });
  });
});
