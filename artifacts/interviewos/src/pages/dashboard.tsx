import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { 
  CheckCircle2, 
  FileQuestion, 
  TrendingUp, 
  Clock, 
  PlayCircle,
  Plus,
  BookOpen,
  History,
  Sparkles
} from 'lucide-react';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { StatCard } from '@/components/shared/StatCard';
import { InterviewCard } from '@/components/shared/InterviewCard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';

const CHART_DATA = [
  { name: 'Mon', score: 65 },
  { name: 'Tue', score: 72 },
  { name: 'Wed', score: 85 },
  { name: 'Thu', score: 82 },
  { name: 'Fri', score: 88 },
  { name: 'Sat', score: 92 },
  { name: 'Sun', score: 89 },
];

const RECENT_INTERVIEWS = [
  { id: '1', role: 'Frontend Engineer', company: 'Stripe', date: 'Today', score: 88, status: 'completed', tags: ['React', 'CSS v4'] },
  { id: '2', role: 'Full Stack Engineer', company: 'Vercel', date: 'Yesterday', score: 92, status: 'completed', tags: ['Next.js', 'Postgres'] },
  { id: '3', role: 'System Design', company: 'Google', date: '3 days ago', score: 75, status: 'completed', tags: ['Caching', 'CDN'] },
  { id: '4', role: 'Behavioral Prep', company: 'Meta', date: 'Next week', score: null, status: 'upcoming', tags: ['Leadership', 'Conflict'] },
] as const;

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const { profile } = useUserStore();

  useEffect(() => {
    setBreadcrumbs(['Dashboard']);
  }, [setBreadcrumbs]);

  return (
    <DashboardLayout>
      <div className="space-y-8 select-none relative">
        {/* Welcome Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground select-text">
              Welcome back, {profile?.name || 'Developer'}
            </h1>
            <p className="text-muted-foreground text-sm mt-1 select-text">
              Analyze your performance, target weaknesses, and master your technical interviews.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              className="rounded-full text-xs gap-1.5 h-9 px-4 border-border"
              onClick={() => setLocation('/interviews/history')}
            >
              <History className="h-4 w-4" />
              History
            </Button>
            <Button 
              onClick={() => setLocation('/interviews/new')}
              className="rounded-full text-xs gap-1.5 h-9 px-5 bg-[#4285F4] hover:bg-[#3b77db] text-white border-0 shadow-sm transition-colors"
            >
              <Plus className="h-4 w-4" />
              New Mock Interview
            </Button>
          </div>
        </div>

        {/* Stats Grid - Google Colors theme mapping */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Questions Solved"
            value="142"
            icon={CheckCircle2}
            trend="+12 this week"
            trendType="positive"
            colorTheme="green"
          />
          <StatCard
            label="Mock Interviews"
            value="18"
            icon={FileQuestion}
            trend="+3 this month"
            trendType="positive"
            colorTheme="blue"
          />
          <StatCard
            label="Success Rate"
            value="84%"
            icon={TrendingUp}
            trend="Top 15% overall"
            trendType="positive"
            colorTheme="yellow"
          />
          <StatCard
            label="Practice Time"
            value="48h"
            icon={Clock}
            trend="4h this week"
            trendType="positive"
            colorTheme="red"
          />
        </div>

        {/* Main Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Sessions */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-foreground">Recent Sessions</h2>
                <p className="text-muted-foreground text-xs font-medium">Your latest mock interview evaluations.</p>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-xs font-semibold text-muted-foreground hover:text-foreground rounded-full"
                onClick={() => setLocation('/interviews/history')}
              >
                View All
              </Button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {RECENT_INTERVIEWS.map((session) => (
                <InterviewCard
                  key={session.id}
                  id={session.id}
                  role={session.role}
                  company={session.company}
                  type={session.id === '3' ? 'system-design' : 'coding'}
                  date={session.date}
                  score={session.score}
                  status={session.status}
                  tags={session.tags as any}
                  onClick={() => setLocation(`/interviews/session/${session.id}`)}
                />
              ))}
            </div>
          </div>

          {/* Performance Chart */}
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-bold text-foreground">Performance Trend</h2>
              <p className="text-muted-foreground text-xs font-medium">Average score progress over last 7 days.</p>
            </div>
            <Card className="h-[270px] rounded-2xl bg-card/60 backdrop-blur-md border border-border/50">
              <CardContent className="p-4 pt-6 h-full flex flex-col justify-between">
                <div className="h-[200px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={CHART_DATA}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                      <XAxis 
                        dataKey="name" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        dy={6}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        domain={[0, 100]}
                      />
                      <Tooltip
                        cursor={{ fill: 'hsl(var(--muted))' }}
                        contentStyle={{ 
                          borderRadius: '12px', 
                          border: '1px solid hsl(var(--border))',
                          background: 'hsl(var(--card))',
                          fontSize: '11px'
                        }}
                      />
                      <Bar 
                        dataKey="score" 
                        radius={[4, 4, 0, 0]} 
                        maxBarSize={30}
                      >
                        {CHART_DATA.map((entry, index) => {
                          const colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335'];
                          return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
export { Dashboard };
