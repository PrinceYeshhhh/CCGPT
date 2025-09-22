import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { ChatPage } from './pages/ChatPage'
import { EmbedPage } from './pages/EmbedPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { BillingPage } from './pages/BillingPage'
import { SettingsPage } from './pages/SettingsPage'
import { LoadingSpinner } from './components/LoadingSpinner'
import ErrorBoundary from './components/ErrorBoundary'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { Navbar } from '@/components/common/Navbar'
import { Footer } from '@/components/common/Footer'
import { Home } from '@/pages/public/Home'
import { Pricing } from '@/pages/public/Pricing'
import { FAQ } from '@/pages/public/FAQ'
import { DashboardLayout } from '@/pages/dashboard/DashboardLayout'
import { DashboardPage } from './pages/DashboardPage'
import { useApiHealth } from '@/hooks/useApiHealth'

function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  )
}

function App() {
  const { user, isLoading } = useAuth()
  useApiHealth()

  if (isLoading) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </ErrorBoundary>
    )
  }

  return (
    <ThemeProvider>
      <ErrorBoundary>
        <Routes>
          {/* Public site */}
          <Route path="/" element={<PublicLayout><Home /></PublicLayout>} />
          <Route path="/pricing" element={<PublicLayout><Pricing /></PublicLayout>} />
          <Route path="/faq" element={<PublicLayout><FAQ /></PublicLayout>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Authenticated dashboard */}
          {user ? (
            <Route path="/dashboard" element={<DashboardLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="embed" element={<EmbedPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="billing" element={<BillingPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          ) : null}

          {/* Fallbacks */}
          <Route path="*" element={<Navigate to={user ? '/dashboard' : '/'} replace />} />
        </Routes>
      </ErrorBoundary>
    </ThemeProvider>
  )
}

export default App
