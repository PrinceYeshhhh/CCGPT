import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'primary'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  default: 'bg-primary text-white hover:bg-primary/90 shadow-sm hover:shadow-md',
  destructive: 'bg-red-600 text-white hover:bg-red-700 shadow-sm hover:shadow-md',
  outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground shadow-sm hover:shadow-md',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm hover:shadow-md',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  link: 'text-primary underline-offset-4 hover:underline',
  primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md dark:bg-blue-500 dark:hover:bg-blue-600',
}

const sizeClasses: Record<NonNullable<ButtonProps['size']>, string> = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3',
  lg: 'h-11 rounded-md px-8',
  icon: 'h-10 w-10',
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
