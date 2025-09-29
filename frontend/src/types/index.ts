export interface User {
  id: string;
  email: string;
  businessName: string;
  plan: 'starter' | 'pro' | 'enterprise';
  createdAt: string;
}

export interface Document {
  id: string;
  name: string;
  status: 'processing' | 'embedded' | 'active' | 'failed';
  uploadedAt: string;
  size: number;
}

export interface Analytics {
  totalQueries: number;
  queriesThisMonth: number;
  topQuestions: Array<{
    question: string;
    count: number;
  }>;
  usage: {
    current: number;
    limit: number;
  };
  chartData: Array<{
    date: string;
    queries: number;
  }>;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  features: string[];
  popular?: boolean;
  stripePriceId: string;
}