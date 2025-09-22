import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, Bot, BarChart3, CreditCard, Zap, Shield, Globe, CheckCircle, ArrowRight } from 'lucide-react';

export function Home() {
  const features = [
    { icon: <Upload className="h-6 w-6" />, title: 'Upload Documents', description: 'Simply upload your FAQs, documentation, or knowledge base files.' },
    { icon: <Bot className="h-6 w-6" />, title: 'AI Chatbot', description: 'Get an intelligent chatbot trained instantly on your content.' },
    { icon: <Globe className="h-6 w-6" />, title: 'Embeddable Widget', description: 'Add the chat widget to your website with a single line of code.' },
    { icon: <BarChart3 className="h-6 w-6" />, title: 'Analytics Dashboard', description: 'Track customer queries, satisfaction, and usage patterns.' },
  ]

  const benefits = [
    '24/7 automated customer support',
    'Reduce support ticket volume by 80%',
    'Instant responses to customer queries',
    'Scale support without hiring more agents',
    'Customizable to match your brand',
    'Enterprise-grade security',
  ]

  return (
    <div className="min-h-screen">
      <section className="relative bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-20 lg:py-32">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6">
              AI Customer Support
              <span className="text-blue-600"> That Actually Works</span>
            </h1>
            <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
              Transform your customer support with AI. Upload your docs, get an intelligent chatbot, and provide 24/7 support that scales with your business.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button size="lg" variant="primary" className="text-lg px-8 py-3 w-full sm:w-auto">
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/pricing">
                <Button size="lg" variant="outline" className="text-lg px-8 py-3 w-full sm:w-auto">
                  View Pricing
                </Button>
              </Link>
            </div>
            <div className="mt-12 flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-6 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center"><CheckCircle className="h-4 w-4 text-green-500 mr-2" />Free 14-day trial</div>
              <div className="flex items-center"><CheckCircle className="h-4 w-4 text-green-500 mr-2" />No credit card required</div>
              <div className="flex items-center"><CheckCircle className="h-4 w-4 text-green-500 mr-2" />Setup in 5 minutes</div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">How It Works</h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">Get your AI customer support up and running in three simple steps</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="text-center">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600 dark:text-blue-400 mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">Transform Your Customer Support</h2>
              <p className="text-lg text-muted-foreground mb-8">Stop losing customers to slow support. CustomerCareGPT provides instant, accurate answers 24/7, reducing your support workload while improving customer satisfaction.</p>
              <div className="grid grid-cols-1 gap-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-foreground">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-8 text-white shadow-2xl">
              <div className="space-y-6">
                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                  <Zap className="h-8 w-8 mb-2" />
                  <h3 className="text-xl font-semibold mb-2">Lightning Fast Setup</h3>
                  <p className="text-blue-100">Get your AI chatbot running in under 5 minutes</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                  <Shield className="h-8 w-8 mb-2" />
                  <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
                  <p className="text-blue-100">Your data is encrypted and secure with SOC 2 compliance</p>
                </div>
                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                  <BarChart3 className="h-8 w-8 mb-2" />
                  <h3 className="text-xl font-semibold mb-2">Powerful Analytics</h3>
                  <p className="text-blue-100">Track performance and optimize customer experience</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-blue-600 dark:bg-blue-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Ready to Transform Your Customer Support?</h2>
          <p className="text-lg md:text-xl text-blue-100 mb-8 max-w-2xl mx-auto">Join thousands of businesses already using CustomerCareGPT to provide exceptional customer support at scale.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-3 w-full sm:w-auto">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/contact">
              <Button size="lg" variant="outline" className="text-lg px-8 py-3 w-full sm:w-auto border-white text-white hover:bg-white hover:text-blue-600">
                Talk to Sales
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
