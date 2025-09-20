import { useQuery } from 'react-query'
import { FileText, MessageCircle, Code, BarChart3, Upload, Plus, TrendingUp, Users, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { AnalyticsOverview, QueryOverTime, TopQuery } from '../types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { formatDate } from '../lib/utils'

export function DashboardPage() {
  const { data: overview, isLoading } = useQuery<AnalyticsOverview>(
    'analytics-summary',
    async () => {
      const response = await api.get('/api/v1/analytics/summary')
      return response.data
    }
  )

  const { data: queriesOverTime } = useQuery<QueryOverTime[]>(
    'queries-over-time',
    async () => {
      const response = await api.get('/api/v1/analytics/queries-over-time?days=7')
      return response.data
    }
  )

  const { data: topQueries } = useQuery<TopQuery[]>(
    'top-queries',
    async () => {
      const response = await api.get('/api/v1/analytics/top-queries?limit=5')
      return response.data
    }
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const stats = [
    {
      name: 'Total Queries',
      value: overview?.total_messages || 0,
      icon: MessageCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      description: 'Past 30 days'
    },
    {
      name: 'Active Sessions',
      value: overview?.active_sessions || 0,
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      description: 'Last 24 hours'
    },
    {
      name: 'Documents',
      value: overview?.total_documents || 0,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      description: 'Knowledge base'
    },
    {
      name: 'Avg Response Time',
      value: overview?.avg_response_time || 0,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      description: `${overview?.avg_response_time || 0}ms`,
      isTime: true
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Welcome to your CustomerCareGPT admin panel
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Link
            to="/documents"
            className="btn btn-primary"
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload Document
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-3 rounded-md ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stat.isTime ? `${stat.value}ms` : stat.value.toLocaleString()}
                  </dd>
                  <dd className="text-xs text-gray-400">
                    {stat.description}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Documents */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
            <Link
              to="/documents"
              className="text-sm text-primary hover:text-primary-600"
            >
              View all
            </Link>
          </div>
          <div className="space-y-3">
            <Link
              to="/documents"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
            >
              <FileText className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Upload Documents</p>
                <p className="text-sm text-gray-500">Add PDF, DOCX, or CSV files</p>
              </div>
            </Link>
            <Link
              to="/embed"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
            >
              <Code className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Create Embed Code</p>
                <p className="text-sm text-gray-500">Generate widget for your website</p>
              </div>
            </Link>
            <Link
              to="/chat"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
            >
              <MessageCircle className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Test Chat</p>
                <p className="text-sm text-gray-500">Try out your AI assistant</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Analytics Summary */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Analytics Summary</h3>
            <Link
              to="/analytics"
              className="text-sm text-primary hover:text-primary-600"
            >
              View details
            </Link>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Active Sessions</span>
              <span className="text-sm font-medium text-gray-900">
                {overview?.active_sessions || 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Avg Response Time</span>
              <span className="text-sm font-medium text-gray-900">
                {overview?.avg_response_time ? `${overview.avg_response_time}ms` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Confidence Level</span>
              <span className={`text-sm font-medium ${
                overview?.avg_confidence === 'high' ? 'text-green-600' :
                overview?.avg_confidence === 'medium' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {overview?.avg_confidence || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Total Chunks</span>
              <span className="text-sm font-medium text-gray-900">
                {overview?.total_chunks || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Top Questions */}
      {topQueries && topQueries.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top 5 Most Asked Questions</h3>
          <div className="space-y-3">
            {topQueries.map((query, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-900 flex-1">{query.query}</p>
                <span className="text-sm text-gray-500 ml-4">{query.count} times</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
