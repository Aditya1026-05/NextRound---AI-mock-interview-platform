import React, { useEffect } from 'react';
import { useUIStore } from '@/store/useUIStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { StatCard } from '@/components/shared/StatCard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, Award, Zap, BrainCircuit, Target, CheckCircle2 } from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';

const SCORE_HISTORY = [
  { week: 'Wk 1', score: 62 },
  { week: 'Wk 2', score: 68 },
  { week: 'Wk 3', score: 75 },
  { week: 'Wk 4', score: 72 },
  { week: 'Wk 5', score: 84 },
  { week: 'Wk 6', score: 88 },
];

const SKILL_MASTERY = [
  { subject: 'Algorithms', A: 90, fullMark: 100 },
  { subject: 'System Design', A: 75, fullMark: 100 },
  { subject: 'Communication', A: 85, fullMark: 100 },
  { subject: 'Concurrency', A: 65, fullMark: 100 },
  { subject: 'Testing', A: 80, fullMark: 100 },
  { subject: 'Database Design', A: 70, fullMark: 100 },
];

export default function Analytics() {
  const { setBreadcrumbs } = useUIStore();

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Performance Analytics']);
  }, [setBreadcrumbs]);

  return (
    <DashboardLayout>
      <div className="space-y-8 select-none">
        <div className="border-b border-border pb-6">
          <h2 className="text-3xl font-extrabold tracking-tight">Performance Analytics</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Deep dive into your technical capability vectors, score improvements, and topic mastery charts.
          </p>
        </div>

        {/* Analytics Top stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            label="Overall Grade"
            value="A-"
            icon={Award}
            trend="Top 12% globally"
            trendType="positive"
          />
          <StatCard
            label="Total Evaluation Loops"
            value="24"
            icon={Target}
            trend="+4 sessions this month"
            trendType="positive"
          />
          <StatCard
            label="Topic Weaknesses"
            value="Concurrency"
            icon={BrainCircuit}
            trend="Needs deep practice"
            trendType="negative"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Historical Score Progression */}
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-foreground">Score Progression</h3>
              <p className="text-muted-foreground text-xs font-medium">Weekly average mock evaluation scores.</p>
            </div>
            <Card className="h-[300px]">
              <CardContent className="p-4 pt-6 h-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={SCORE_HISTORY}>
                    <defs>
                      <linearGradient id="scoreColor" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="week" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      contentStyle={{ 
                        borderRadius: '8px', 
                        border: '1px solid hsl(var(--border))',
                        background: 'hsl(var(--card))',
                        fontSize: '11px'
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="score" 
                      stroke="hsl(var(--chart-1))" 
                      fillOpacity={1} 
                      fill="url(#scoreColor)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Radar skill mastery distribution */}
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-foreground">Skill Vector Distribution</h3>
              <p className="text-muted-foreground text-xs font-medium">Evaluation metrics mapping across key engineering axes.</p>
            </div>
            <Card className="h-[300px]">
              <CardContent className="p-4 pt-6 h-full flex justify-center items-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={SKILL_MASTERY}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis 
                      dataKey="subject" 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10, fontWeight: 500 }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 9 }} />
                    <Radar 
                      name="Alex Developer" 
                      dataKey="A" 
                      stroke="hsl(var(--chart-2))" 
                      fill="hsl(var(--chart-2))" 
                      fillOpacity={0.2} 
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
export { Analytics };
