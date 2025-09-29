import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Zap, 
  MousePointer, 
  AlertTriangle, 
  Clock, 
  Cpu, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Download,
  Settings,
  CheckCircle
} from 'lucide-react';
import { usePerformance } from '@/hooks/usePerformance';
import { api } from '@/lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface PerformanceData {
  summary: {
    performance_score: number;
    avg_lcp: number;
    avg_fid: number;
    avg_cls: number;
    avg_fcp: number;
    avg_ttfb: number;
    avg_page_load_time: number;
    avg_api_response_time: number;
    total_errors: number;
    error_rate: number;
    is_healthy: boolean;
    health_issues: string[];
  };
  trends: {
    lcp: Array<{ date: string; value: number }>;
    fid: Array<{ date: string; value: number }>;
    cls: Array<{ date: string; value: number }>;
    errors: Array<{ date: string; value: number }>;
  };
  alerts: Array<{
    id: string;
    alert_type: string;
    severity: string;
    message: string;
    created_at: string;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export function Performance() {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');
  const [refreshing, setRefreshing] = useState(false);

  const { 
    metrics, 
    getPerformanceSummary, 
    getPerformanceScore,
    reportMetrics 
  } = usePerformance();

  const realTimeSummary = getPerformanceSummary();
  const realTimeScore = getPerformanceScore();

  const fetchData = async () => {
    try {
      setLoading(true);
      const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
      
      const [summaryRes, trendsRes, alertsRes] = await Promise.all([
        api.get('/performance/summary', { params: { days } }),
        api.get('/performance/trends', { params: { days } }),
        api.get('/performance/alerts')
      ]);

      setData({
        summary: summaryRes.data,
        trends: trendsRes.data.trends,
        alerts: alertsRes.data
      });
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await reportMetrics(); // Report current real-time metrics
    await fetchData();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default';
    if (score >= 70) return 'secondary';
    return 'destructive';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Performance Analytics</h1>
          <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Performance Analytics</h1>
          <p className="text-gray-600 mt-1">
            Monitor and analyze your application's performance metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Real-time Performance Monitor */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Real-time Performance
          </CardTitle>
          <CardDescription>
            Current performance metrics from your browser
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Performance Score</span>
                <Badge variant={getScoreBadgeVariant(realTimeScore)}>
                  {realTimeScore}/100
                </Badge>
              </div>
              <Progress value={realTimeScore} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Zap className="h-4 w-4 text-blue-600" />
                <span>LCP</span>
              </div>
              <div className="text-2xl font-bold">{realTimeSummary.lcp}</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <MousePointer className="h-4 w-4 text-green-600" />
                <span>FID</span>
              </div>
              <div className="text-2xl font-bold">{realTimeSummary.fid}</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 text-orange-600" />
                <span>CLS</span>
              </div>
              <div className="text-2xl font-bold">{realTimeSummary.cls}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Analytics */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Performance Score Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{data?.summary.performance_score || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {data?.summary.is_healthy ? 'Healthy' : 'Needs Attention'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data?.summary.avg_api_response_time ? 
                    `${Math.round(data.summary.avg_api_response_time)}ms` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  API Response Time
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data?.summary.error_rate ? 
                    `${(data.summary.error_rate * 100).toFixed(2)}%` : '0%'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {data?.summary.total_errors || 0} total errors
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Page Load</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data?.summary.avg_page_load_time ? 
                    `${Math.round(data.summary.avg_page_load_time)}ms` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Average Load Time
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Core Web Vitals */}
          <Card>
            <CardHeader>
              <CardTitle>Core Web Vitals</CardTitle>
              <CardDescription>
                Key performance indicators for user experience
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="h-4 w-4 text-blue-600" />
                    <span>LCP</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data?.summary.avg_lcp ? `${Math.round(data.summary.avg_lcp)}ms` : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">Largest Contentful Paint</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <MousePointer className="h-4 w-4 text-green-600" />
                    <span>FID</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data?.summary.avg_fid ? `${Math.round(data.summary.avg_fid)}ms` : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">First Input Delay</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <AlertTriangle className="h-4 w-4 text-orange-600" />
                    <span>CLS</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data?.summary.avg_cls ? data.summary.avg_cls.toFixed(3) : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">Cumulative Layout Shift</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-purple-600" />
                    <span>FCP</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data?.summary.avg_fcp ? `${Math.round(data.summary.avg_fcp)}ms` : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">First Contentful Paint</div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Cpu className="h-4 w-4 text-indigo-600" />
                    <span>TTFB</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {data?.summary.avg_ttfb ? `${Math.round(data.summary.avg_ttfb)}ms` : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">Time to First Byte</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          {/* Performance Trends Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>LCP Trend</CardTitle>
                <CardDescription>Largest Contentful Paint over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data?.trends.lcp || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#0088FE" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>FID Trend</CardTitle>
                <CardDescription>First Input Delay over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data?.trends.fid || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#00C49F" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>CLS Trend</CardTitle>
                <CardDescription>Cumulative Layout Shift over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={data?.trends.cls || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#FFBB28" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Trend</CardTitle>
                <CardDescription>Errors over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data?.trends.errors || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#FF8042" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Alerts</CardTitle>
              <CardDescription>
                Active performance alerts and notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data?.alerts && data.alerts.length > 0 ? (
                <div className="space-y-4">
                  {data.alerts.map((alert) => (
                    <div key={alert.id} className="flex items-start gap-4 p-4 border rounded-lg">
                      <div className="flex-shrink-0">
                        <AlertTriangle className="h-5 w-5 text-orange-600" />
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{alert.alert_type}</h4>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{alert.message}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">No Active Alerts</h3>
                  <p className="text-gray-500">Your performance is looking good!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Recommendations</CardTitle>
              <CardDescription>
                Actionable insights to improve your application's performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data?.summary.health_issues && data.summary.health_issues.length > 0 ? (
                  data.summary.health_issues.map((issue, index) => (
                    <div key={index} className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-yellow-800">Performance Issue</h4>
                        <p className="text-sm text-yellow-700 mt-1">{issue}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">No Issues Found</h3>
                    <p className="text-gray-500">Your application is performing well!</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
