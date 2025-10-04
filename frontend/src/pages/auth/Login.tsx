import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot, Mail, Lock, User, Phone } from 'lucide-react';
import { api, setAuthToken } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

const loginSchema = z.object({
  usernameOrEmail: z.string().min(3, 'Username or email is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

export function Login() {
  const navigate = useNavigate();
  const { login: setSession } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      const payload = data.usernameOrEmail.includes('@')
        ? { email: data.usernameOrEmail, password: data.password }
        : { email: data.usernameOrEmail, password: data.password };
      const response = await api.post('/auth/login', payload);
      const token = response.data?.access_token || response.data?.accessToken || response.data?.token;
      if (token) {
        setAuthToken(token);
        setSession(token, { username: data.usernameOrEmail });
      }
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Bot className="h-12 w-12 text-blue-600" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-foreground">
          Sign in to your account
        </h2>
        <p className="mt-2 text-center text-sm text-foreground">
          Don't have an account?{' '}
          <Link to="/register" className="font-medium text-gradient">
            Sign up
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <CardHeader>
            <CardTitle>Welcome back</CardTitle>
            <CardDescription>
              Enter your email and password to access your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

              <div>
                <label htmlFor="usernameOrEmail" className="block text-sm font-medium text-foreground mb-2">
                  Username or Email
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="usernameOrEmail"
                    {...register('usernameOrEmail')}
                    placeholder="Enter your username or email"
                    className="pl-10"
                  />
                </div>
                {errors.usernameOrEmail && (
                  <p className="text-red-600 text-sm mt-1">{errors.usernameOrEmail.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    {...register('password')}
                    type="password"
                    placeholder="Enter your password"
                    className="pl-10"
                  />
                </div>
                {errors.password && (
                  <p className="text-red-600 text-sm mt-1">{errors.password.message}</p>
                )}
              </div>


              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-input bg-background rounded"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-foreground">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <a href="#" className="font-medium text-foreground">
                    Forgot your password?
                  </a>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110" 
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Demo Account</span>
                </div>
              </div>

              <div className="mt-3 text-center text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                <p><strong>Demo credentials:</strong></p>
                <p>Username: demo</p>
                <p>Password: demo123</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}