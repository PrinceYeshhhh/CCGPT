import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Download, 
  TrendingUp, 
  Users, 
  MessageSquare, 
  Clock,
  Filter,
  Calendar
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '@/lib/api';

export function Analytics() {
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: '7d',
    queryType: 'all',
    userType: 'all',
    satisfaction: 'all'
  });
  const [queryData, setQueryData] = useState<any[]>([]);
  const [hourlyData, setHourlyData] = useState<any[]>([]);
  const [topQuestions, setTopQuestions] = useState<any[]>([]);
  const [satisfactionData, setSatisfactionData] = useState<any[]>([
    { name: 'Satisfied', value: 0, color: '#10b981' },
    { name: 'Neutral', value: 0, color: '#f59e0b' },
    { name: 'Unsatisfied', value: 0, color: '#ef4444' }
  ]);
  const [metrics, setMetrics] = useState({
    totalQueries: 0,
    uniqueUsers: 0,
    avgResponseTime: 0,
    satisfactionRate: 0
  });

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
        
        // Use the detailed analytics endpoints for the Analytics page
        const [overviewRes, usageRes, hourlyRes, satRes, topQuestionsRes] = await Promise.all([
          api.get('/analytics/detailed-overview', { params: { days } }),
          api.get('/analytics/detailed-usage-stats', { params: { days } }),
          api.get('/analytics/detailed-hourly', { params: { days } }),
          api.get('/analytics/detailed-satisfaction', { params: { days } }),
          api.get('/analytics/detailed-top-questions', { params: { days, limit: 10 } })
        ]);

        // Process overview data for key metrics
        const overview = overviewRes.data?.data || {};
        setMetrics({
          totalQueries: overview.total_queries || 0,
          uniqueUsers: overview.unique_users || 0,
          avgResponseTime: overview.avg_response_time || 0,
          satisfactionRate: overview.satisfaction_rate || 0
        });

        // Process usage data for charts
        const usage = (usageRes.data?.data || []).map((d: any) => ({
          date: String(d.date),
          queries: d.queries ?? 0,
          satisfied: d.satisfied ?? 0,
          unsatisfied: d.unsatisfied ?? 0,
        }));
        setQueryData(usage);

        // Process hourly data
        const hourly = (hourlyRes.data?.data || []).map((h: any) => ({ 
          hour: h.hour, 
          queries: h.queries ?? 0 
        }));
        setHourlyData(hourly);

        // Process top questions
        const tq = (topQuestionsRes.data?.data || []).map((q: any) => ({
          question: q.question ?? 'Question',
          count: q.count ?? 0,
          satisfaction: q.satisfaction ?? 90,
        }));
        setTopQuestions(tq);

        // Process satisfaction data
        const satSeries = (satRes.data?.data || []);
        const satSum = satSeries.reduce((acc: any, d: any) => ({
          satisfied: acc.satisfied + (d.satisfied ?? 0),
          unsatisfied: acc.unsatisfied + (d.unsatisfied ?? 0),
        }), { satisfied: 0, unsatisfied: 0 });
        
        const total = satSum.satisfied + satSum.unsatisfied;
        const satisfiedPct = total > 0 ? Math.round((satSum.satisfied / total) * 100) : 0;
        const unsatisfiedPct = total > 0 ? Math.round((satSum.unsatisfied / total) * 100) : 0;
        
        setSatisfactionData([
          { name: 'Satisfied', value: satisfiedPct, color: '#10b981' },
          { name: 'Neutral', value: Math.max(0, 100 - satisfiedPct - unsatisfiedPct), color: '#f59e0b' },
          { name: 'Unsatisfied', value: unsatisfiedPct, color: '#ef4444' }
        ]);

      } catch (e) {
        console.error('Failed to load analytics data:', e);
        // Keep default values on error
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [timeRange]);

  const exportData = async () => {
    try {
      const res = await api.get('/analytics/detailed-export', { params: { format: 'json' } });
      const dataStr = 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(res.data?.data ?? {}));
      const a = document.createElement('a');
      a.href = dataStr;
      a.download = 'analytics.json';
      a.click();
    } catch (e) {}
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Analytics</h1>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowFilterModal(true)}
          >
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
          <div className="flex items-center space-x-1">
            <Button 
              variant={timeRange === '7d' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setTimeRange('7d')}
            >
              <Calendar className="mr-2 h-4 w-4" />
              7 days
            </Button>
            <Button 
              variant={timeRange === '30d' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setTimeRange('30d')}
            >
              30 days
            </Button>
            <Button 
              variant={timeRange === '90d' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setTimeRange('90d')}
            >
              90 days
            </Button>
          </div>
          <Button onClick={exportData} size="sm" className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : metrics.totalQueries.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12%</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : metrics.uniqueUsers.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+8%</span> from last week
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
              {loading ? '...' : `${metrics.avgResponseTime.toFixed(1)}s`}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">-0.3s</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Satisfaction Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : `${metrics.satisfactionRate.toFixed(1)}%`}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2.1%</span> from last week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
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
              <CardTitle>Query Volume Over Time</CardTitle>
              <CardDescription>Daily queries and satisfaction rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-muted-foreground">Loading chart data...</div>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={queryData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" className="text-muted-foreground" />
                      <YAxis className="text-muted-foreground" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="queries" 
                        stackId="1"
                        stroke="#3b82f6" 
                        fill="#3b82f6"
                        fillOpacity={0.6}
                      />
                    </AreaChart>
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
                <CardTitle>Customer Satisfaction</CardTitle>
                <CardDescription>Overall satisfaction breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {loading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-muted-foreground">Loading satisfaction data...</div>
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={satisfactionData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {satisfactionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <div className="flex justify-center space-x-6 mt-4">
                  {satisfactionData.map((item) => (
                    <div key={item.name} className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-muted-foreground">
                        {item.name}: {item.value}%
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Satisfaction Trend</CardTitle>
                <CardDescription>Satisfied vs unsatisfied queries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {loading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-muted-foreground">Loading satisfaction trend...</div>
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={queryData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="date" className="text-muted-foreground" />
                        <YAxis className="text-muted-foreground" />
                        <Tooltip />
                        <Area 
                          type="monotone" 
                          dataKey="satisfied" 
                          stackId="1"
                          stroke="#10b981" 
                          fill="#10b981"
                          fillOpacity={0.6}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="unsatisfied" 
                          stackId="1"
                          stroke="#ef4444" 
                          fill="#ef4444"
                          fillOpacity={0.6}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="hourly" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Hourly Query Distribution</CardTitle>
              <CardDescription>Query volume by hour of day</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-muted-foreground">Loading hourly trends...</div>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={hourlyData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="hour" className="text-muted-foreground" />
                      <YAxis className="text-muted-foreground" />
                      <Tooltip />
                      <Bar dataKey="queries" fill="#3b82f6" radius={[4, 4, 0, 0]} />
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
              <CardTitle>Top Questions</CardTitle>
              <CardDescription>Most frequently asked questions and their satisfaction rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {loading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-muted-foreground">Loading top questions...</div>
                  </div>
                ) : topQuestions.length === 0 ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-muted-foreground">No questions found for the selected period</div>
                  </div>
                ) : (
                  topQuestions.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-sm mb-1">{item.question}</p>
                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <span>{item.count} times asked</span>
                          <span className="flex items-center">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
                            {item.satisfaction}% satisfied
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div 
                            className="bg-primary h-2 rounded-full" 
                            style={{ width: `${topQuestions[0].count > 0 ? (item.count / topQuestions[0].count) * 100 : 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Filter Modal */}
      {showFilterModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Filter Analytics</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Date Range</label>
                <select 
                  value={filters.dateRange}
                  onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="90d">Last 90 days</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Query Type</label>
                <select 
                  value={filters.queryType}
                  onChange={(e) => setFilters({...filters, queryType: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="all">All Queries</option>
                  <option value="general">General</option>
                  <option value="support">Support</option>
                  <option value="sales">Sales</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">User Type</label>
                <select 
                  value={filters.userType}
                  onChange={(e) => setFilters({...filters, userType: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="all">All Users</option>
                  <option value="new">New Users</option>
                  <option value="returning">Returning Users</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Satisfaction</label>
                <select 
                  value={filters.satisfaction}
                  onChange={(e) => setFilters({...filters, satisfaction: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="all">All Ratings</option>
                  <option value="satisfied">Satisfied</option>
                  <option value="neutral">Neutral</option>
                  <option value="unsatisfied">Unsatisfied</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <Button 
                variant="outline" 
                onClick={() => setShowFilterModal(false)}
              >
                Cancel
              </Button>
              <Button 
                onClick={() => {
                  setTimeRange(filters.dateRange);
                  setShowFilterModal(false);
                  // Apply filters logic here
                }}
                className="bg-gradient-to-br from-[#4285F4] to-[#A142F4] text-white border-0 hover:brightness-110"
              >
                Apply Filters
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}