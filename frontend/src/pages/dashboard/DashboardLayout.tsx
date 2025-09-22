import React from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { Sidebar } from '@/components/dashboard/Sidebar'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { User, LogOut, Bell, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'

export function DashboardLayout() {
  const navigate = useNavigate()
  const { logout, user } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-card border-b border-border px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <div className="relative max-w-md w-full sm:w-auto">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input placeholder="Search documents, queries..." className="pl-10 pr-4 w-full" />
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <ThemeToggle />
              <Button variant="ghost" size="icon" className="hidden sm:flex"><Bell className="h-5 w-5" /></Button>
              <div className="hidden md:flex items-center space-x-3">
                <div className="text-right hidden lg:block">
                  <p className="text-sm font-medium text-gray-900">{user?.full_name || 'User'}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <Button variant="ghost" size="icon"><User className="h-5 w-5" /></Button>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout}><LogOut className="h-5 w-5" /></Button>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
