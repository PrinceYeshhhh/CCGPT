import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(({ className, value = 0, ...props }, ref) => {
  return (
    <div ref={ref} className={cn('relative h-4 w-full overflow-hidden rounded-full bg-secondary', className)} {...props}>
      <div className="h-full bg-primary transition-all duration-300" style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
    </div>
  )
})

Progress.displayName = 'Progress'
