import { cn } from '../lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  message?: string
}

export function LoadingSpinner({ size = 'md', className, message }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <div
        role="status"
        aria-label="Loading"
        className={cn(
          'animate-spin rounded-full border-2 border-gray-300 border-t-primary',
          sizeClasses[size],
          className
        )}
      />
      {message && (
        <p className="text-sm text-gray-600">{message}</p>
      )}
    </div>
  )
}
