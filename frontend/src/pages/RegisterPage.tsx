import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2, ArrowLeft } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { cn } from '../lib/utils'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

interface RegisterForm {
  email: string
  password: string
  confirmPassword: string
  full_name?: string
  business_name?: string
  business_domain?: string
}

export function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { register: registerUser } = useAuth()

  const form = useForm<RegisterForm>()

  const handleRegister = async (data: RegisterForm) => {
    if (data.password !== data.confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setIsLoading(true)
    try {
      const result = await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        business_name: data.business_name,
        business_domain: data.business_domain,
      })
      
      if (result.success) {
        toast.success('Registration successful! Please login.')
        // Redirect to login page
        window.location.href = '/login'
      } else {
        toast.error(result.error || 'Registration failed')
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              to="/login"
              className="font-medium text-primary hover:text-primary-600"
            >
              sign in to existing account
            </Link>
          </p>
        </div>

        <div className="mt-8 space-y-6">
          <form className="space-y-6" onSubmit={form.handleSubmit(handleRegister)}>
            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <input
                {...form.register('email', { 
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                type="email"
                autoComplete="email"
                className="input mt-1"
                placeholder="Enter your email"
              />
              {form.formState.errors.email && (
                <p className="mt-1 text-sm text-red-600">
                  {form.formState.errors.email.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="full_name" className="label">
                Full Name (Optional)
              </label>
              <input
                {...form.register('full_name')}
                type="text"
                className="input mt-1"
                placeholder="Enter your full name"
              />
            </div>

            <div>
              <label htmlFor="business_name" className="label">
                Business Name (Optional)
              </label>
              <input
                {...form.register('business_name')}
                type="text"
                className="input mt-1"
                placeholder="Enter your business name"
              />
            </div>

            <div>
              <label htmlFor="business_domain" className="label">
                Business Domain (Optional)
              </label>
              <input
                {...form.register('business_domain')}
                type="text"
                className="input mt-1"
                placeholder="Enter your business domain"
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  {...form.register('password', { 
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Password must be at least 8 characters' }
                  })}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  className="input pr-10"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {form.formState.errors.password && (
                <p className="mt-1 text-sm text-red-600">
                  {form.formState.errors.password.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Confirm Password
              </label>
              <input
                {...form.register('confirmPassword', { 
                  required: 'Please confirm your password'
                })}
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                className="input mt-1"
                placeholder="Confirm your password"
              />
              {form.formState.errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">
                  {form.formState.errors.confirmPassword.message}
                </p>
              )}
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary w-full btn-lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
