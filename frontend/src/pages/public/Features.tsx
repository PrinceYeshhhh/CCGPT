import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Upload, 
  Bot, 
  BarChart3, 
  Globe,
  Zap,
  Shield,
  Palette,
  MessageSquare,
  FileText,
  Settings,
  Users,
  Code,
  CheckCircle,
  ArrowRight,
  LayoutDashboard
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { PostLoginTrialPopup } from '@/components/common/PostLoginTrialPopup';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export function Features() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [showTrialPopup, setShowTrialPopup] = useState(false);
  const [hasActiveSubscription, setHasActiveSubscription] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      checkSubscriptionStatus();
    }
  }, [isAuthenticated]);

  const checkSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/billing/status');
      const billingInfo = response.data;
      
      const hasValidSubscription = 
        billingInfo.plan === 'free_trial' && billingInfo.status === 'trialing' ||
        billingInfo.plan === 'starter' && billingInfo.status === 'active' ||
        billingInfo.plan === 'pro' && billingInfo.status === 'active' ||
        billingInfo.plan === 'enterprise' && billingInfo.status === 'active' ||
        billingInfo.plan === 'white_label' && billingInfo.status === 'active';

      setHasActiveSubscription(hasValidSubscription);
    } catch (error) {
      console.error('Failed to check subscription status:', error);
      setHasActiveSubscription(false);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTrial = () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (hasActiveSubscription) {
      navigate('/dashboard');
      return;
    }
    
    setShowTrialPopup(true);
  };

  const handleTrialSuccess = () => {
    setShowTrialPopup(false);
    navigate('/dashboard');
  };

  const coreFeatures = [
    {
      icon: <Upload className="h-8 w-8" />,
      title: 'Smart Document Processing',
      description: 'Upload FAQs, documentation, or knowledge base files in multiple formats (PDF, DOC, TXT, MD). Our AI instantly processes and chunks your content for optimal chatbot training.',
      benefits: ['Multiple file format support', 'Automatic content chunking', 'Instant processing', 'Unlimited uploads (plan dependent)']
    },
    {
      icon: <Bot className="h-8 w-8" />,
      title: 'AI-Powered Chatbot',
      description: 'Get an intelligent chatbot trained instantly on your content. Provides accurate, contextual responses to customer queries 24/7 without human intervention.',
      benefits: ['Instant training on your content', '24/7 automated responses', 'Contextual understanding', 'Multi-language support']
    },
    {
      icon: <Globe className="h-8 w-8" />,
      title: 'Embeddable Widget',
      description: 'Add our customizable chat widget to your website with a single line of code. Fully responsive and matches your brand identity.',
      benefits: ['One-line integration', 'Fully customizable design', 'Mobile responsive', 'Brand matching']
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: 'Advanced Analytics',
      description: 'Track customer queries, satisfaction rates, usage patterns, and popular questions. Export data and gain insights to improve your support.',
      benefits: ['Real-time analytics', 'Customer satisfaction tracking', 'Usage insights', 'Data export capabilities']
    }
  ];

  const advancedFeatures = [
    {
      icon: <Palette className="h-6 w-6" />,
      title: 'Custom Branding',
      description: 'Customize colors, logo, welcome messages, and widget positioning to match your brand perfectly.'
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: 'Enterprise Security',
      description: 'SOC 2 compliant with end-to-end encryption. Your data and customer conversations are always secure.'
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: 'Lightning Fast',
      description: 'Average response time under 1.2 seconds. Your customers get instant answers to their questions.'
    },
    {
      icon: <Code className="h-6 w-6" />,
      title: 'API Access',
      description: 'Full REST API access for custom integrations and advanced use cases (Pro plan and above).'
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: 'Team Collaboration',
      description: 'Invite team members, manage permissions, and collaborate on customer support content.'
    },
    {
      icon: <Settings className="h-6 w-6" />,
      title: 'Advanced Configuration',
      description: 'Fine-tune response behavior, set custom triggers, and configure advanced chatbot settings.'
    }
  ];

  const useCases = [
    {
      title: 'E-commerce Support',
      description: 'Handle product inquiries, shipping questions, and return policies automatically.',
      icon: '🛒'
    },
    {
      title: 'SaaS Documentation',
      description: 'Turn your product documentation into an interactive help assistant.',
      icon: '💻'
    },
    {
      title: 'Customer Service',
      description: 'Reduce support ticket volume by 80% with instant, accurate responses.',
      icon: '🎧'
    },
    {
      title: 'Educational Content',
      description: 'Create interactive learning assistants from your educational materials.',
      icon: '📚'
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary/10 via-background to-accent/10 dark:from-primary/20 dark:via-background dark:to-accent/5 py-20 lg:py-32">
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            Powerful Features for
            <span className="text-gradient text-gradient-shine"> Modern Customer Support</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Discover how CustomerCareGPT transforms your customer support with AI-powered automation, 
            advanced analytics, and seamless integrations.
          </p>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Core Features
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
              Everything you need to automate and scale your customer support
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {coreFeatures.map((feature, index) => (
              <Card key={index} className="hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="w-16 h-16 bg-primary/10 dark:bg-primary/20 rounded-xl flex items-center justify-center text-icon mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl mb-2">{feature.title}</CardTitle>
                  <CardDescription className="text-base leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feature.benefits.map((benefit, idx) => (
                      <li key={idx} className="flex items-center text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                        <span className="text-foreground">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Advanced Features */}
      <section className="py-20 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Advanced Capabilities
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
              Professional features for businesses that demand more
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {advancedFeatures.map((feature, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 rounded-lg flex items-center justify-center text-white mb-4 bg-gradient-to-br from-[#4285F4] to-[#A142F4]">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Perfect for Every Industry
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
              See how businesses across different industries use CustomerCareGPT
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {useCases.map((useCase, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="text-4xl mb-4">{useCase.icon}</div>
                  <CardTitle className="text-lg">{useCase.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                    {useCase.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="py-20 bg-brand text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Easy Integration, Powerful Results
              </h2>
              <p className="text-lg mb-8 text-white/90">
                Get your AI customer support up and running in minutes, not hours. 
                Our simple integration process means you can start helping customers immediately.
              </p>
              <div className="space-y-4">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-bold mr-4">1</div>
                  <span className="text-white">Upload your documents and FAQs</span>
                </div>
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-bold mr-4">2</div>
                  <span className="text-white">Customize your chat widget</span>
                </div>
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-bold mr-4">3</div>
                  <span className="text-white">Add one line of code to your website</span>
                </div>
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-bold mr-4">4</div>
                  <span className="text-white">Start providing 24/7 AI support</span>
                </div>
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 mb-6">
                <div className="text-gray-500">// Add to your website</div>
                <div className="text-green-400">&lt;script src="https://widget.customercaregpt.com/widget.js"</div>
                <div className="ml-8">data-widget-id="your-widget-id"&gt;</div>
                <div className="text-green-400">&lt;/script&gt;</div>
              </div>
              <p className="text-white/90 text-sm">
                That's it! Your AI customer support is now live and ready to help your customers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-background">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Ready to Transform Your Customer Support?
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mb-8">
            Join thousands of businesses already using CustomerCareGPT to provide 
            exceptional customer support at scale.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated && hasActiveSubscription ? (
              <Button 
                size="lg"
                className="px-8 py-3 w-full sm:w-auto bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
                onClick={() => navigate('/dashboard')}
              >
                <LayoutDashboard className="mr-2 h-5 w-5" />
                Go to Dashboard
              </Button>
            ) : (
              <Button 
                size="lg"
                className="px-8 py-3 w-full sm:w-auto bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
                onClick={handleStartTrial}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="mr-2 h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Loading...
                  </>
                ) : (
                  <>
                    Start Free Trial
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            )}
            <Link to="/pricing">
              <Button 
                size="lg"
                variant="outline"
                className="px-8 py-3 w-full sm:w-auto"
              >
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Trial Popup */}
      <PostLoginTrialPopup
        isOpen={showTrialPopup}
        onClose={() => setShowTrialPopup(false)}
        onSuccess={handleTrialSuccess}
      />
    </div>
  );
}