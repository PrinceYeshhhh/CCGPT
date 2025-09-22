import { useQuery } from 'react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TrendingUp, MessageSquare, Users, Clock, Download, Filter, Calendar } from 'lucide-react'
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { api } from '@/lib/api'

interface AnalyticsOverview { total_messages: number; active_sessions: number; total_documents: number; avg_response_time: number; avg_confidence?: number }
interface QueryOverTime { date: string; sessions: number; messages: number }
interface TopQuery { query: string; count: number }
interface FileUsage { name: string; usage_count: number; percentage: number }
interface ResponseQuality { confidence_distribution: { confidence: string; count: number }[] }

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export function Analytics() {
  const { data: overview, isLoading: overviewLoading } = useQuery<AnalyticsOverview>('analytics-summary', async () => {
    const res = await api.get('/api/v1/analytics/summary')
    return res.data
  })

  const { data: queriesOverTime, isLoading: queriesLoading } = useQuery<QueryOverTime[]>('queries-over-time', async () => {
    const res = await api.get('/api/v1/analytics/queries-over-time?days=30')
    return res.data
  })

  const { data: topQueries, isLoading: topQueriesLoading } = useQuery<TopQuery[]>('top-queries', async () => {
    const res = await api.get('/api/v1/analytics/top-queries?limit=10')
    return res.data
  })

  const { data: fileUsage, isLoading: fileUsageLoading } = useQuery<FileUsage[]>('file-usage', async () => {
    const res = await api.get('/api/v1/analytics/file-usage?days=30')
    return res.data
  })

  const { data: responseQuality, isLoading: qualityLoading } = useQuery<ResponseQuality>('response-quality', async () => {
    const res = await api.get('/api/v1/analytics/response-quality?days=30')
    return res.data
  })

  const exportData = () => {
    // Optional: trigger a backend export endpoint
    window.print()
  }

  if (overviewLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Analytics</h1>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm"><Filter className="mr-2 h-4 w-4" />Filter</Button>
          <Button variant="outline" size="sm"><Calendar className="mr-2 h-4 w-4" />Last 30 days</Button>
          <Button onClick={exportData} size="sm"><Download className="mr-2 h-4 w-4" />Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_messages ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.active_sessions ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_documents ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.avg_response_time ?? 0}ms</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="queries" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="queries">Query Volume</TabsTrigger>
          <TabsTrigger value="satisfaction">Satisfaction</TabsTrigger>
          <TabsTrigger value="hourly">Hourly Trends</TabsTrigger>
          <TabsTrigger value="questions">Top Questions</TabsTrigger>
        </TabsList>

        <TabsContent value="queries" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Queries Over Time</CardTitle>
              <CardDescription>Daily sessions and messages</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                {queriesLoading ? (
                  <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
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
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="satisfaction" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Response Quality</CardTitle>
                <CardDescription>Confidence distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {qualityLoading ? (
                    <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie dataKey="count" data={responseQuality?.confidence_distribution || []} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5}>
                          {(responseQuality?.confidence_distribution || []).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Overview</CardTitle>
                <CardDescription>Satisfaction snapshot</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold text-foreground">{overview?.avg_confidence ?? 'N/A'}</div>
                  <div className="text-sm text-muted-foreground">Average Confidence</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="hourly" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Queries</CardTitle>
              <CardDescription>Most frequent questions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                {topQueriesLoading ? (
                  <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={(topQueries || []).slice(0, 10)} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="query" type="category" width={160} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="questions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>File Usage</CardTitle>
              <CardDescription>Breakdown by file type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {fileUsageLoading ? (
                  <div className="flex items-center justify-center h-full"><LoadingSpinner size="lg" /></div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie dataKey="usage_count" data={fileUsage || []} cx="50%" cy="50%" outerRadius={100} label>
                        {(fileUsage || []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
