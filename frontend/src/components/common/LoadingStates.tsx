import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface LoadingCardProps {
  title?: string;
  className?: string;
}

export function LoadingCard({ title, className }: LoadingCardProps) {
  return (
    <Card className={cn("animate-pulse", className)}>
      <CardHeader className="space-y-2">
        {title && <CardTitle className="text-sm">{title}</CardTitle>}
        <Skeleton className="h-4 w-1/3" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-3 w-24" />
      </CardContent>
    </Card>
  );
}

export function LoadingSpinner({ size = "default", className }: { size?: "sm" | "default" | "lg"; className?: string }) {
  const sizeClasses = {
    sm: "h-4 w-4",
    default: "h-6 w-6",
    lg: "h-8 w-8"
  };

  return (
    <div className={cn("animate-spin rounded-full border-2 border-gray-300 border-t-blue-600", sizeClasses[size], className)} />
  );
}

export function LoadingChart({ className }: { className?: string }) {
  return (
    <Card className={cn("animate-pulse", className)}>
      <CardHeader>
        <CardTitle className="text-sm">Loading Chart</CardTitle>
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardContent>
    </Card>
  );
}

export function LoadingTable({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex space-x-4">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-4 w-1/4" />
        </div>
      ))}
    </div>
  );
}

export function LoadingList({ items = 3, className }: { items?: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function LoadingForm({ fields = 4, className }: { fields?: number; className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      <div className="flex space-x-2 pt-4">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-20" />
      </div>
    </div>
  );
}

export function LoadingPage({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 w-48" />
        <div className="flex space-x-2">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-24" />
        </div>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
      </div>
      
      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LoadingCard title="Chart" />
        <LoadingCard title="List" />
      </div>
    </div>
  );
}

export function LoadingOverlay({ message = "Loading...", className }: { message?: string; className?: string }) {
  return (
    <div className={cn("fixed inset-0 bg-black/50 flex items-center justify-center z-50", className)}>
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 flex items-center space-x-3">
        <LoadingSpinner />
        <span className="text-sm font-medium">{message}</span>
      </div>
    </div>
  );
}

export function LoadingButton({ 
  loading, 
  children, 
  className,
  ...props 
}: { 
  loading: boolean; 
  children: React.ReactNode; 
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={cn(
        "inline-flex items-center justify-center",
        loading && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {loading && <LoadingSpinner size="sm" className="mr-2" />}
      {children}
    </button>
  );
}