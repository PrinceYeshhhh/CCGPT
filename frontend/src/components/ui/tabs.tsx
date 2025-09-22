import * as React from 'react'
import { cn } from '@/lib/utils'

interface TabsProps {
  children: React.ReactNode
  defaultValue?: string
  className?: string
}

export const Tabs = ({ children, defaultValue, className }: TabsProps) => (
  <div className={cn(className)} data-default-value={defaultValue}>{children}</div>
)

export const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground w-full sm:w-auto overflow-x-auto', className)} {...props} />
))
TabsList.displayName = 'TabsList'

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value?: string
}
export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(({ className, ...props }, ref) => (
  <button ref={ref} className={cn('inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all duration-200 data-[state=active]:bg-background data-[state=active]:text-foreground shadow-sm', className)} {...props} />
))
TabsTrigger.displayName = 'TabsTrigger'

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string
}
export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('mt-2', className)} {...props} />
))
TabsContent.displayName = 'TabsContent'
