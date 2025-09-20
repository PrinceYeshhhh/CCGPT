export interface User {
  id: number
  email: string
  full_name?: string
  business_name?: string
  business_domain?: string
  subscription_plan: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at?: string
}

export interface Document {
  id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  status: 'uploaded' | 'processing' | 'processed' | 'error'
  processing_error?: string
  title?: string
  description?: string
  tags?: string[]
  created_at: string
  updated_at?: string
  processed_at?: string
  chunks_count?: number
}

export interface DocumentChunk {
  id: number
  chunk_index: number
  content: string
  page_number?: number
  section_title?: string
  word_count?: number
  created_at: string
}

export interface ChatSession {
  id: number
  session_id: string
  is_active: boolean
  created_at: string
  updated_at?: string
  ended_at?: string
  message_count: number
  messages?: ChatMessage[]
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  model_used?: string
  response_time_ms?: number
  tokens_used?: number
  sources_used?: any[]
  confidence_score?: 'high' | 'medium' | 'low'
  is_flagged: boolean
  created_at: string
}

export interface EmbedCode {
  id: number
  code_name: string
  widget_config: WidgetConfig
  embed_script: string
  embed_html?: string
  is_active: boolean
  usage_count: number
  last_used?: string
  created_at: string
  updated_at?: string
}

export interface WidgetConfig {
  title: string
  placeholder: string
  primary_color: string
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  show_avatar: boolean
  avatar_url?: string
  welcome_message: string
  max_messages: number
  enable_sound: boolean
  enable_typing_indicator: boolean
}

export interface AnalyticsOverview {
  total_documents: number
  total_chunks: number
  total_sessions: number
  total_messages: number
  active_sessions: number
  avg_response_time: number
  avg_confidence: string
  top_questions: Array<{
    question: string
    count: number
  }>
}

export interface QueryOverTime {
  date: string
  messages: number
  sessions: number
}

export interface TopQuery {
  query: string
  count: number
}

export interface FileUsage {
  filename: string
  usage_count: number
  percentage: number
}

export interface EmbedCodeAnalytics {
  total_embed_codes: number
  active_embed_codes: number
  total_usage: number
  embed_codes: Array<{
    id: string
    name: string
    is_active: boolean
    usage_count: number
    last_used: string | null
    created_at: string
  }>
}

export interface ResponseQuality {
  confidence_distribution: Array<{
    confidence: string
    count: number
  }>
  avg_response_time_by_confidence: Array<{
    confidence: string
    avg_time: number
  }>
}

export interface UsageStats {
  date: string
  sessions_count: number
  messages_count: number
  documents_uploaded: number
  avg_session_duration: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}
