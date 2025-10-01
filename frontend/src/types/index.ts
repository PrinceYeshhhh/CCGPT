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

// API Response Types
export interface ApiDocument {
  id?: string;
  document_id?: string;
  uuid?: string;
  name?: string;
  filename?: string;
  status?: 'processing' | 'embedded' | 'active' | 'failed';
  created_at?: string;
  uploaded_at?: string;
  size?: number;
}

export interface ApiAnalyticsOverview {
  total_messages?: number;
  active_sessions?: number;
  avg_response_time?: number;
  top_questions?: Array<{
    question: string;
    count: number;
  }>;
}

export interface ApiUsageStats {
  date: string;
  messages_count: number;
}

export interface ApiKpis {
  queries?: {
    delta_pct: number;
  };
  sessions?: {
    delta_pct: number;
  };
  avg_response_time_ms?: {
    delta_ms: number;
  };
  active_sessions?: {
    delta: number;
  };
}

export interface ApiBillingInfo {
  plan?: string;
  status?: string;
  is_trial?: boolean;
  trial_end?: string;
  usage?: {
    queries_used: number;
    queries_limit: number;
  };
}

export interface ApiEmbedCode {
  id: string;
  code_name: string;
  embed_script: string;
  is_active: boolean;
  usage_count: number;
}

export interface ApiWorkspaceSettings {
  id: string;
  name?: string;
  settings?: Record<string, unknown>;
}

export interface ApiNotification {
  id: number;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: 'info' | 'warning' | 'success' | 'error';
}

export interface ApiError {
  detail?: string;
  message?: string;
  code?: string;
  field?: string;
}

export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface ApiErrorResponse {
  response?: {
    status: number;
    data: ApiError;
    headers: Record<string, string>;
  };
  request?: unknown;
  message: string;
}