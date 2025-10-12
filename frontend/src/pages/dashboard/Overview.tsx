import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  MessageSquare, 
  Users, 
  TrendingUp, 
  Clock,
  ArrowUpRight,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoadingCard, LoadingSpinner, LoadingChart } from '@/components/common/LoadingStates';
import { CurrentPlanDisplay } from '@/components/dashboard/CurrentPlanDisplay';
import toast from 'react-hot-toast';
import { 
  ApiAnalyticsOverview, 
  ApiUsageStats, 
  ApiKpis, 
  ApiBillingInfo, 
  ApiResponse 
} from '@/types';

export function Overview() {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);
  const [stats, setStats] = React.useState({
    totalQueries: 0,
    queriesThisMonth: 0,
    activeUsers: 0,
    avgResponseTime: '—',
    usage: { current: 0, limit: 1000 },
    deltas: { queriesPct: 0, sessionsPct: 0, responseMs: 0, activeDelta: 0 },
  });
  const [topQuestions, setTopQuestions] = React.useState<{ question: string; count: number }[]>([]);
  const [chartData, setChartData] = React.useState<{ date: string; queries: number }[]>([]);
  const [billingInfo, setBillingInfo] = React.useState<ApiBillingInfo | null>(null);

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const [overviewRes, usage7dRes, usage30dRes, kpisRes, billingInfoRes] = await Promise.all([
        api.get('/analytics/overview'),
        api.get('/analytics/usage-stats', { params: { days: 7 } }),
        api.get('/analytics/usage-stats', { params: { days: 30 } }),
        api.get('/analytics/kpis', { params: { days: 30 } }),
        api.get('/billing/status'),
      ]);

      const o: ApiAnalyticsOverview = overviewRes.data || {};
      const k: ApiKpis = kpisRes.data || {};
      const b: ApiBillingInfo = billingInfoRes.data || {};
      setBillingInfo(b);
      const monthlyQueries = (usage30dRes.data as ApiUsageStats[] || []).reduce((acc: number, d: ApiUsageStats) => acc + (d.messages_count ?? 0), 0);
      const limit = Number(b?.usage?.queries_limit ?? 1000);
      const used = Number(b?.usage?.queries_used ?? monthlyQueries);
      
      setStats({
        totalQueries: o.total_messages ?? 0,
        queriesThisMonth: used,
        activeUsers: o.active_sessions ?? 0,
        avgResponseTime: o.avg_response_time ? `${(Number(o.avg_response_time) / 1000).toFixed(1)}s` : '—',
        usage: { current: used, limit },
        deltas: {
          queriesPct: k?.queries?.delta_pct ?? 0,
          sessionsPct: k?.sessions?.delta_pct ?? 0,
          responseMs: (k?.avg_response_time_ms?.delta_ms ?? 0),
          activeDelta: k?.active_sessions?.delta ?? 0,
        },
      });
      
      const tq = (o.top_questions || []).slice(0, 5).map((q: any) => ({ 
        question: q.question ?? 'Question', 
        count: q.count ?? 0 
      }));
      setTopQuestions(tq);
      
      const u = (usage7dRes.data as ApiUsageStats[] || []).map((d: ApiUsageStats) => ({ 
        date: String(d.date), 
        queries: d.messages_count ?? 0 
      }));
      setChartData(u);
      
    } catch (e: any) {
      console.error('Failed to fetch overview data:', e);
      const errorMessage = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed to load dashboard data';
      setError(errorMessage);
      
      if (isRefresh) {
        toast.error(`Refresh failed: ${errorMessage}`);
      } else {
        toast.error('Failed to load dashboard data');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const usagePercentage = stats.usage.limit > 0 ? (stats.usage.current / stats.usage.limit) * 100 : 0;

  const formatDeltaPct = (value: number) => `${value >= 0 ? '+' : ''}${value}%`;
  const formatDeltaSeconds = (ms: number) => {
    const s = (ms / 1000);
    const sign = s === 0 ? '' : (s > 0 ? '+' : '');
    return `${sign}${s.toFixed(1)}s`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Dashboard Overview</h1>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" disabled>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Refresh
            </Button>
            <Button 
              className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
              onClick={() => navigate('/pricing')}
            >
              Upgrade Plan
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingCard title="Usage Chart" />
          <LoadingCard title="Top Questions" />
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Dashboard Overview</h1>
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                {billingInfo && (
                  <CurrentPlanDisplay
                    plan={billingInfo.plan || 'free'}
                    status={billingInfo.status || 'active'}
                    isTrial={billingInfo.is_trial || false}
                    trialEnd={billingInfo.trial_end}
                    className="sm:w-48"
                  />
                )}
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fetchData(true)}
                    disabled={refreshing}
                  >
                    <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                  <Button
                    className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
                    onClick={() => navigate('/pricing')}
                  >
                    Upgrade Plan
                    <ArrowUpRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => fetchData()}
                disabled={loading || refreshing}
                className="ml-auto"
              >
                {loading || refreshing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  'Retry'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalQueries.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {formatDeltaPct(stats.deltas.queriesPct)} from previous period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.queriesThisMonth.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {formatDeltaPct(stats.deltas.queriesPct)} from previous period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeUsers}</div>
            <p className="text-xs text-muted-foreground">
              {stats.deltas.activeDelta >= 0 ? `+${stats.deltas.activeDelta}` : stats.deltas.activeDelta} from previous period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgResponseTime}</div>
            <p className="text-xs text-muted-foreground">
              {formatDeltaSeconds(stats.deltas.responseMs)} from previous period
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Usage and Chart Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Query Volume</CardTitle>
            <CardDescription>Daily queries over the last week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="queries" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Usage This Month</CardTitle>
            <CardDescription>Query limit usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span>Queries used</span>
                <span>{stats.usage.current} / {stats.usage.limit}</span>
              </div>
              <Progress value={usagePercentage} className="h-2" />
              <div className="flex items-center text-sm text-muted-foreground">
                {usagePercentage > 80 && (
                  <>
                    <AlertCircle className="h-4 w-4 text-orange-500 mr-2" />
                    <span className="text-orange-600">High usage - consider upgrading</span>
                  </>
                )}
                {usagePercentage <= 80 && (
                  <span>{Math.round(100 - usagePercentage)}% remaining</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Top Questions This Month</CardTitle>
          <CardDescription>Most frequently asked questions by your customers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topQuestions.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <span className="font-medium text-sm">{item.question}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-muted-foreground">{item.count} times</span>
                  <div className="w-16 bg-muted rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(item.count / topQuestions[0].count) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      </div>
    </ErrorBoundary>
  );
}