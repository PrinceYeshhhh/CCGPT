import { useQuery } from 'react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, MessageCircle, FileText, Users, Clock, Target } from 'lucide-react'
import { api } from '../lib/api'
import { AnalyticsOverview, QueryOverTime, TopQuery, FileUsage, ResponseQuality } from '../types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { formatDate } from '../lib/utils'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export function AnalyticsPage() {
  const { data: overview, isLoading: overviewLoading } = useQuery<AnalyticsOverview>(
    'analytics-summary',
    async () => {
      const response = await api.get('/api/v1/analytics/summary')
      return response.data
    }
  )

  const { data: queriesOverTime, isLoading: queriesLoading } = useQuery<QueryOverTime[]>(
    'queries-over-time',
    async () => {
      const response = await api.get('/api/v1/analytics/queries-over-time?days=30')
      return response.data
    }
  )

  const { data: topQueries, isLoading: topQueriesLoading } = useQuery<TopQuery[]>(
    'top-queries',
    async () => {
      const response = await api.get('/api/v1/analytics/top-queries?limit=10')
      return response.data
    }
  )

  const { data: fileUsage, isLoading: fileUsageLoading } = useQuery<FileUsage[]>(
    'file-usage',
    async () => {
      const response = await api.get('/api/v1/analytics/file-usage?days=30')
      return response.data
    }
  )

  const { data: responseQuality, isLoading: qualityLoading } = useQuery<ResponseQuality>(
    'response-quality',
    async () => {
      const response = await api.get('/api/v1/analytics/response-quality?days=30')
      return response.data
    }
  )

  if (overviewLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
        <p className="text-gray-500">Track your AI assistant's performance and usage</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="p-3 rounded-md bg-blue-100">
                <MessageCircle className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Queries</dt>
                <dd className="text-lg font-medium text-gray-900">{overview?.total_messages || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="p-3 rounded-md bg-green-100">
                <Users className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Active Sessions</dt>
                <dd className="text-lg font-medium text-gray-900">{overview?.active_sessions || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="p-3 rounded-md bg-purple-100">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Documents</dt>
                <dd className="text-lg font-medium text-gray-900">{overview?.total_documents || 0}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="p-3 rounded-md bg-orange-100">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Avg Response Time</dt>
                <dd className="text-lg font-medium text-gray-900">{overview?.avg_response_time || 0}ms</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Queries Over Time</h3>
          {queriesLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={queriesOverTime || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="sessions" stroke="#3b82f6" strokeWidth={2} name="Sessions" />
                <Line type="monotone" dataKey="messages" stroke="#10b981" strokeWidth={2} name="Messages" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Queries</h3>
          {topQueriesLoading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topQueries?.slice(0, 5) || []} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="query" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* File Usage Chart */}
      {fileUsage && fileUsage.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">File Usage</h3>
            {fileUsageLoading ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={fileUsage}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name} (${percentage}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="usage_count"
                  >
                    {fileUsage.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Response Quality</h3>
            {qualityLoading ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900">
                    {overview?.avg_confidence || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">Average Confidence</div>
                </div>
                {responseQuality?.confidence_distribution && (
                  <div className="space-y-2">
                    {responseQuality.confidence_distribution.map((item, index) => (
                      <div key={item.confidence} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 capitalize">{item.confidence}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${(item.count / responseQuality.confidence_distribution.reduce((sum, c) => sum + c.count, 0)) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-500 w-8">{item.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Questions */}
      {topQueries && topQueries.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Questions</h3>
          <div className="space-y-3">
            {topQueries.slice(0, 10).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-900 flex-1">{item.query}</p>
                <span className="text-sm text-gray-500 ml-4">{item.count} times</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
