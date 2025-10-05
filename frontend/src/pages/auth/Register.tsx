import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot, Mail, Lock, Building, Globe, User, Phone } from 'lucide-react';
import { api } from '@/lib/api';

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  mobile: z.string().min(10, 'Mobile number must be at least 10 digits'),
  otp: z.string().min(4, 'OTP must be at least 4 digits'),
  organization: z.string().min(2, 'Organization name must be at least 2 characters'),
  domain: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterForm = z.infer<typeof registerSchema>;

export function Register() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        full_name: data.username,
        business_name: data.organization,
        business_domain: data.domain,
        mobile_phone: data.mobile,
        otp_code: data.otp,
      });
      navigate('/login');
    } catch (error) {
      // Error handling is done by the API interceptor
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Bot className="h-12 w-12 text-blue-600" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-foreground">
          Start your 7-day free trial
        </h2>
        <p className="mt-2 text-center text-sm text-foreground">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-gradient">
            Login
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <CardHeader>
            <CardTitle>Create your account</CardTitle>
            <CardDescription>
              Get started with CustomerCareGPT in seconds
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
             <div>
               <label htmlFor="username" className="block text-sm font-medium text-foreground mb-2">
                 Username
               </label>
               <div className="relative">
                 <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                 <Input
                   {...register('username')}
                   placeholder="Choose a username"
                   className="pl-10"
                 />
               </div>
               {errors.username && (
                 <p className="text-red-600 text-sm mt-1">{errors.username.message}</p>
               )}
             </div>

             <div>
               <label htmlFor="mobile" className="block text-sm font-medium text-foreground mb-2">
                 Mobile Number
               </label>
               <div className="relative">
                 <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                 <Input
                   {...register('mobile')}
                   type="tel"
                   placeholder="Enter your mobile number"
                   className="pl-10"
                 />
               </div>
               {errors.mobile && (
                 <p className="text-red-600 text-sm mt-1">{errors.mobile.message}</p>
               )}
             </div>

             <div>
               <label htmlFor="otp" className="block text-sm font-medium text-foreground mb-2">
                 OTP Verification
               </label>
               <div className="flex space-x-2">
                 <div className="relative flex-1">
                   <Input
                     {...register('otp')}
                     type="text"
                     placeholder="Enter OTP"
                     maxLength={6}
                   />
                 </div>
                <Button type="button" size="sm" className="whitespace-nowrap bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110" onClick={async () => {
                  try {
                    const phone = (document.getElementsByName('mobile')[0] as HTMLInputElement)?.value;
                    await api.post('/auth/send-otp', { mobile_phone: phone });
                  } catch (e) {
                    // Error handling is done by the API interceptor
                  }
                }}>
                  Send OTP
                </Button>
               </div>
               {errors.otp && (
                 <p className="text-red-600 text-sm mt-1">{errors.otp.message}</p>
               )}
               <p className="text-xs text-muted-foreground mt-1">
                 We'll send a verification code to your mobile number
               </p>
             </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                  Email address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    {...register('email')}
                    type="email"
                    placeholder="Enter your email"
                    className="pl-10"
                  />
                </div>
                {errors.email && (
                  <p className="text-red-600 text-sm mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    {...register('password')}
                    type="password"
                    placeholder="Create a password"
                    className="pl-10"
                  />
                </div>
                {errors.password && (
                  <p className="text-red-600 text-sm mt-1">{errors.password.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-2">
                  Confirm password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    {...register('confirmPassword')}
                    type="password"
                    placeholder="Confirm your password"
                    className="pl-10"
                  />
                </div>
                {errors.confirmPassword && (
                  <p className="text-red-600 text-sm mt-1">{errors.confirmPassword.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="organization" className="block text-sm font-medium text-foreground mb-2">
                  Organization
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    {...register('organization')}
                    placeholder="Enter your organization name"
                    className="pl-10"
                  />
                </div>
                {errors.organization && (
                  <p className="text-red-600 text-sm mt-1">{errors.organization.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="domain" className="block text-sm font-medium text-foreground mb-2">
                  Domain (Optional)
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    {...register('domain')}
                    placeholder="company.com"
                    className="pl-10"
                  />
                </div>
                {errors.domain && (
                  <p className="text-red-600 text-sm mt-1">{errors.domain.message}</p>
                )}
              </div>

              <div className="flex items-center">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-input bg-background rounded"
                  required
                />
                <label htmlFor="terms" className="ml-2 block text-sm text-foreground">
                  I agree to the{' '}
                  <a href="#" className="text-blue-600 hover:text-blue-500">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="#" className="text-blue-600 hover:text-blue-500">
                    Privacy Policy
                  </a>
                </label>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110" 
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Creating account...' : 'Start 7-day free trial'}
              </Button>
            </form>

            <div className="mt-6">
              <div className="relative mb-3">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Trial Details</span>
                </div>
              </div>
              <div className="text-center text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                <p><strong>7-day free trial</strong></p>
                <p>No credit card required</p>
                <p>Cancel anytime</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}