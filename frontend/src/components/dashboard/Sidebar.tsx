import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, FileText, Code, BarChart3, CreditCard, Settings, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Documents', href: '/dashboard/documents', icon: FileText },
  { name: 'Embed Widget', href: '/dashboard/embed', icon: Code },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  return (
    <div className="hidden lg:flex flex-col w-64 bg-card border-r border-border min-h-screen">
      <div className="flex items-center px-6 py-4 border-b">
        <Bot className="h-8 w-8 text-blue-600" />
        <span className="ml-2 text-lg font-semibold text-foreground">CustomerCareGPT</span>
      </div>
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
                isActive ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="px-4 py-4 border-t">
        <div className="bg-blue-50 dark:bg-blue-950/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Starter Plan</p>
              <p className="text-xs text-blue-600 dark:text-blue-300">389 / 1,000 queries</p>
            </div>
            <Link to="/dashboard/billing">
              <button className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition-colors">Upgrade</button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
