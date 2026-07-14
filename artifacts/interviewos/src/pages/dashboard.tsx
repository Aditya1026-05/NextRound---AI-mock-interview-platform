import * as React from "react"
import { Link } from "wouter"
import { FileQuestion, TrendingUp, CheckCircle2, Clock, PlayCircle, BarChart3 } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const MOCK_STATS = [
  { label: "Questions Solved", value: "142", icon: CheckCircle2, trend: "+12 this week" },
  { label: "Mock Interviews", value: "18", icon: FileQuestion, trend: "+3 this month" },
  { label: "Success Rate", value: "84%", icon: TrendingUp, trend: "Top 15% overall" },
  { label: "Practice Time", value: "48h", icon: Clock, trend: "4h this week" },
]

const MOCK_SESSIONS = [
  { id: "1", role: "Frontend Engineer", company: "Stripe", date: "Today", score: 88, status: "completed" },
  { id: "2", role: "Full Stack Engineer", company: "Vercel", date: "Yesterday", score: 92, status: "completed" },
  { id: "3", role: "System Design", company: "Google", date: "3 days ago", score: 75, status: "completed" },
  { id: "4", role: "Behavioral", company: "General", date: "Next week", score: null, status: "upcoming" },
]

const MOCK_CHART_DATA = [
  { name: "Mon", score: 65 },
  { name: "Tue", score: 72 },
  { name: "Wed", score: 85 },
  { name: "Thu", score: 82 },
  { name: "Fri", score: 88 },
  { name: "Sat", score: 92 },
  { name: "Sun", score: 89 },
]

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Welcome back, Alex</h1>
          <p className="text-muted-foreground mt-1">Here is a summary of your interview preparation.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline">Resume Last Session</Button>
          <Button className="gap-2">
            <PlayCircle className="w-4 h-4" />
            New Mock Interview
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {MOCK_STATS.map((stat, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1 font-medium">{stat.trend}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Table */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Sessions</CardTitle>
                <CardDescription>Your latest mock interviews and practices.</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/sessions/all">View All</Link>
              </Button>
            </CardHeader>
            <CardContent className="flex-1">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role / Type</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {MOCK_SESSIONS.map((session) => (
                    <TableRow key={session.id}>
                      <TableCell className="font-medium">
                        <Link href={`/sessions/${session.id}`} className="hover:underline">
                          {session.role}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {session.company !== "General" && (
                            <span className="w-4 h-4 bg-secondary rounded-sm flex items-center justify-center text-[10px] font-bold">
                              {session.company[0]}
                            </span>
                          )}
                          {session.company}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{session.date}</TableCell>
                      <TableCell className="text-right">
                        {session.status === "upcoming" ? (
                          <Badge variant="outline">Upcoming</Badge>
                        ) : (
                          <Badge variant={session.score && session.score > 80 ? "success" : "warning"}>
                            {session.score}/100
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Progress Chart */}
        <div className="space-y-4">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Performance Trend
              </CardTitle>
              <CardDescription>Average scores over the last 7 days.</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-end min-h-[250px]">
              <div className="h-[200px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={MOCK_CHART_DATA}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <Tooltip
                      cursor={{ fill: 'hsl(var(--muted))' }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid hsl(var(--border))' }}
                    />
                    <Bar 
                      dataKey="score" 
                      fill="hsl(var(--primary))" 
                      radius={[4, 4, 0, 0]} 
                      maxBarSize={40}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
