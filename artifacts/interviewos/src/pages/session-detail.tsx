import { useParams } from "wouter"
import { ArrowLeft, CheckCircle2, Clock, PlayCircle, FileText, BarChart3, MessageSquare } from "lucide-react"
import { Link } from "wouter"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export default function SessionDetail() {
  const { id } = useParams()
  
  // Dummy data
  const session = {
    id,
    title: "System Design: News Feed",
    company: "Meta",
    date: "October 12, 2023",
    duration: "45m 12s",
    score: 88,
    metrics: [
      { name: "Communication", score: 92 },
      { name: "Technical Accuracy", score: 85 },
      { name: "Problem Solving", score: 90 },
      { name: "Code Quality", score: 80 }
    ]
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Breadcrumb/Nav */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild className="rounded-full">
          <Link href="/dashboard"><ArrowLeft className="h-5 w-5" /></Link>
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{session.title}</h1>
            <Badge variant="secondary">{session.company}</Badge>
          </div>
          <p className="text-muted-foreground text-sm flex items-center gap-2 mt-1">
            <Clock className="w-4 h-4" /> {session.date} • {session.duration}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column - Score & Metrics */}
        <div className="space-y-6 md:col-span-1">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Overall Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <div className="relative w-32 h-32 flex items-center justify-center rounded-full border-8 border-primary/20 mb-4">
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                  <circle 
                    cx="60" cy="60" r="56" 
                    fill="transparent" 
                    stroke="hsl(var(--primary))" 
                    strokeWidth="8" 
                    strokeDasharray="351.85" 
                    strokeDashoffset={351.85 - (351.85 * session.score) / 100}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <span className="text-4xl font-bold text-foreground">{session.score}</span>
              </div>
              <Badge variant="success" className="text-sm px-3 py-1">Strong Hire</Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5 mt-4">
              {session.metrics.map((metric) => (
                <div key={metric.name} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-muted-foreground">{metric.name}</span>
                    <span className="font-bold">{metric.score}%</span>
                  </div>
                  <Progress value={metric.score} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Tabs for Transcript, Notes, Feedback */}
        <div className="md:col-span-2">
          <Card className="h-full">
            <Tabs defaultValue="transcript" className="w-full">
              <CardHeader className="border-b pb-0 pt-4 px-6 flex flex-row items-center justify-between bg-muted/20">
                <TabsList className="bg-transparent h-12 p-0 space-x-6">
                  <TabsTrigger 
                    value="transcript" 
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Transcript
                  </TabsTrigger>
                  <TabsTrigger 
                    value="feedback" 
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    AI Feedback
                  </TabsTrigger>
                </TabsList>
                <Button variant="outline" size="sm" className="mb-2">
                  <PlayCircle className="w-4 h-4 mr-2" /> Play Audio
                </Button>
              </CardHeader>

              <CardContent className="p-6">
                <TabsContent value="transcript" className="mt-0 space-y-6">
                  {/* Chat Bubbles */}
                  <div className="flex gap-4">
                    <Avatar className="w-8 h-8 border">
                      <AvatarFallback className="bg-primary/10 text-primary font-bold text-xs">AI</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">Interviewer</span>
                        <span className="text-xs text-muted-foreground">00:12</span>
                      </div>
                      <div className="bg-secondary rounded-2xl rounded-tl-none p-4 text-sm text-foreground">
                        Let's design a news feed system like Twitter or Facebook. How would you approach the high-level architecture?
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4 flex-row-reverse">
                    <Avatar className="w-8 h-8 border">
                      <AvatarFallback className="bg-muted text-muted-foreground text-xs font-bold">ME</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-2 flex flex-col items-end">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">00:45</span>
                        <span className="font-semibold text-sm">You</span>
                      </div>
                      <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-none p-4 text-sm max-w-[85%] text-left">
                        Sure. I'll start by clarifying the requirements. For a news feed, the core features would be publishing a post and retrieving a feed of posts from people a user follows. We need to handle high read volume, so it should be highly available. 
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-4 flex-row-reverse">
                    <div className="w-8 h-8" />
                    <div className="flex-1 space-y-2 flex flex-col items-end mt-[-16px]">
                      <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-none rounded-br-none p-4 text-sm max-w-[85%] text-left">
                        I'd propose a fan-out on write approach for standard users, and fan-out on read for celebrities with millions of followers.
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <Avatar className="w-8 h-8 border">
                      <AvatarFallback className="bg-primary/10 text-primary font-bold text-xs">AI</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">Interviewer</span>
                        <span className="text-xs text-muted-foreground">01:30</span>
                      </div>
                      <div className="bg-secondary rounded-2xl rounded-tl-none p-4 text-sm text-foreground">
                        That makes sense. Can you dive deeper into the fan-out on write component? How does the data flow when a standard user creates a post?
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="feedback" className="mt-0 space-y-6">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-lg flex items-center gap-2 text-success">
                      <CheckCircle2 className="w-5 h-5" /> What you did well
                    </h3>
                    <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-5">
                      <li>Excellent requirement gathering at the beginning.</li>
                      <li>Clear explanation of the hybrid fan-out approach.</li>
                      <li>Good awareness of trade-offs between storage and latency.</li>
                    </ul>
                  </div>

                  <div className="space-y-4 pt-4 border-t">
                    <h3 className="font-semibold text-lg flex items-center gap-2 text-warning">
                      <BarChart3 className="w-5 h-5" /> Areas for improvement
                    </h3>
                    <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-5">
                      <li>You spent too much time on the API design and had to rush the database schema.</li>
                      <li>Could have mentioned caching strategies for the feed earlier.</li>
                      <li>When discussing load balancing, specify the algorithms (e.g., Round Robin vs Least Connections).</li>
                    </ul>
                  </div>
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>
        </div>
      </div>
    </div>
  )
}
