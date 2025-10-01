import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import ReactLazy, { Suspense, lazy } from 'react';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { initErrorMonitoring, ErrorBoundary, ErrorFallback } from '@/lib/error-monitoring';

// Public pages
const Home = lazy(() => import('@/pages/public/Home').then(m => ({ default: m.Home })));
const Features = lazy(() => import('@/pages/public/Features').then(m => ({ default: m.Features })));
const Pricing = lazy(() => import('@/pages/public/Pricing').then(m => ({ default: m.Pricing })));
const FAQ = lazy(() => import('@/pages/public/FAQ').then(m => ({ default: m.FAQ })));
const Login = lazy(() => import('@/pages/auth/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('@/pages/auth/Register').then(m => ({ default: m.Register })));
const UserProfile = lazy(() => import('@/pages/public/UserProfile').then(m => ({ default: m.UserProfile })));

// Dashboard pages
const DashboardLayout = lazy(() => import('@/pages/dashboard/DashboardLayout').then(m => ({ default: m.DashboardLayout })));
const Overview = lazy(() => import('@/pages/dashboard/Overview').then(m => ({ default: m.Overview })));
const Documents = lazy(() => import('@/pages/dashboard/Documents').then(m => ({ default: m.Documents })));
const Embed = lazy(() => import('@/pages/dashboard/Embed').then(m => ({ default: m.Embed })));
const Analytics = lazy(() => import('@/pages/dashboard/Analytics').then(m => ({ default: m.Analytics })));
const Performance = lazy(() => import('@/pages/dashboard/Performance').then(m => ({ default: m.Performance })));
const Billing = lazy(() => import('@/pages/dashboard/Billing').then(m => ({ default: m.Billing })));
const Settings = lazy(() => import('@/pages/dashboard/Settings').then(m => ({ default: m.Settings })));

// Layout components
import { Navbar } from '@/components/common/Navbar';
import { Footer } from '@/components/common/Footer';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';
import { NotFound } from '@/components/common/NotFound';
import { AuthProvider } from '@/contexts/AuthContext';
import { PerformanceMonitor } from '@/components/common/PerformanceMonitor';

// Initialize error monitoring
initErrorMonitoring();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

// Mock auth state - in real app, this would come from context/state management
// Real auth now comes from AuthProvider

function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}


function App() {
  // console.log('App component rendering'); // Disabled for performance
  
  return (
    <ErrorBoundary fallback={ErrorFallback}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Router>
              <div className="App">
                <ErrorBoundary>
                  <Suspense fallback={
                    <div className="min-h-screen flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-600">Loading CustomerCareGPT...</p>
                      </div>
                    </div>
                  }>
                    <Routes>
                      {/* Public routes */}
                      <Route path="/" element={
                        <PublicLayout>
                          <Home />
                        </PublicLayout>
                      } />
                      <Route path="/features" element={
                        <PublicLayout>
                          <Features />
                        </PublicLayout>
                      } />
                      <Route path="/pricing" element={
                        <PublicLayout>
                          <Pricing />
                        </PublicLayout>
                      } />
                      <Route path="/faq" element={
                        <PublicLayout>
                          <FAQ />
                        </PublicLayout>
                      } />
                      
                      {/* Auth routes */}
                      <Route path="/login" element={<Login />} />
                      <Route path="/register" element={<Register />} />
                      <Route path="/profile" element={<PublicLayout><UserProfile /></PublicLayout>} />
                      
                      {/* Dashboard routes */}
                      <Route element={<ProtectedRoute />}> 
                        <Route path="/dashboard" element={<DashboardLayout />}>
                          <Route index element={<Overview />} />
                          <Route path="documents" element={<Documents />} />
                          <Route path="embed" element={<Embed />} />
                          <Route path="analytics" element={<Analytics />} />
                          <Route path="performance" element={<Performance />} />
                          <Route path="billing" element={<Billing />} />
                          <Route path="settings" element={<Settings />} />
                        </Route>
                      </Route>
                      
                      {/* Redirect unknown routes to home */}
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Suspense>
                </ErrorBoundary>
                
                <Toaster 
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: '#363636',
                      color: '#fff',
                    },
                  }}
                />
                
                {/* Performance Monitor - Disabled for better performance */}
                {false && process.env.NODE_ENV === 'development' && (
                  <div className="fixed bottom-4 right-4 z-50">
                    <PerformanceMonitor showDetails={false} className="w-80" />
                  </div>
                )}
              </div>
            </Router>
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;