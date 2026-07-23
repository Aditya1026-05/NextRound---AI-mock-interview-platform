import React, { useState, useEffect } from "react"
import { useParams, useLocation } from "wouter"
import { 
  ArrowLeft, 
  CheckCircle2, 
  Clock, 
  FileText, 
  BarChart3, 
  MessageSquare, 
  Star, 
  AlertCircle, 
  Loader2,
  ChevronDown,
  ChevronUp
} from "lucide-react"
import { Link } from "wouter"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { apiFetch } from "@/lib/apiFetch"
import { useUIStore } from "@/store/useUIStore"
import { DashboardLayout } from "@/components/layouts/DashboardLayout"

interface TimelineReview {
  question: string
  answer: string
  score: number
  ideal_answer: string
  evaluation: string
  strengths: string[]
  improvements: string[]
}

interface EvaluationData {
  id: string
  session_id: string
  overall_score: number
  recommendation: string
  summary: string | null
  skill_scores: Record<string, number>
  timeline_reviews: TimelineReview[]
  evaluation_version: string
}

export default function SessionDetail() {
  const { id } = useParams()
  const [, setLocation] = useLocation()
  const { setBreadcrumbs } = useUIStore()

  const [session, setSession] = useState<any>(null)
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [generationStatus, setGenerationStatus] = useState<string>("Loading session...")
  const [error, setError] = useState<string | null>(null)
  
  // Accordion state for timeline reviews
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0)

  useEffect(() => {
    setBreadcrumbs(["Mock Interviews", "Session Evaluation"])
  }, [setBreadcrumbs])

  useEffect(() => {
    if (!id) return

    async function loadData() {
      try {
        setLoading(true)
        setError(null)
        
        // 1. Fetch Session Metadata
        setGenerationStatus("Fetching session details...")
        let sessionRes
        try {
          const res = await apiFetch(`/interview/session/${id}`)
          sessionRes = await res.json()
          setSession(sessionRes)
        } catch (e: any) {
          throw new Error(`Failed to load session: ${e.message}`)
        }

        // 2. Fetch or Generate Evaluation
        setGenerationStatus("Checking for existing evaluation...")
        let evalData: EvaluationData | null = null
        
        try {
          const res = await apiFetch(`/interview/session/${id}/evaluation`)
          evalData = await res.json()
        } catch (e: any) {
          // If 404, it means it doesn't exist. Trigger generation.
          if (e.status === 404) {
            setGenerationStatus("Synthesizing evaluation report (this may take up to 30 seconds)...")
            const generateRes = await apiFetch(`/interview/session/${id}/evaluate`, {
              method: "POST"
            })
            evalData = await generateRes.json()
          } else {
            throw e
          }
        }
        
        setEvaluation(evalData)
      } catch (e: any) {
        console.error(e)
        setError(e.message || "An error occurred while loading the evaluation.")
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [id])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-6">
        <Loader2 className="w-12 h-12 text-[#4285F4] animate-spin" />
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-foreground">NextRound Evaluation Engine</h3>
          <p className="text-muted-foreground text-sm max-w-md">{generationStatus}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto mt-12">
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader className="flex flex-row items-center gap-3">
            <AlertCircle className="w-8 h-8 text-destructive" />
            <div>
              <CardTitle className="text-destructive">Failed to Load Evaluation</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{error}</p>
            <div className="flex gap-3">
              <Button onClick={() => window.location.reload()} variant="outline">
                Retry
              </Button>
              <Button asChild>
                <Link href="/dashboard">Back to Dashboard</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!session || !evaluation) return null

  // Helper for recommendation badges styling
  const getRecBadgeVariant = (rec: string) => {
    switch (rec) {
      case "Strong Hire":
        return "success"
      case "Hire":
        return "success"
      case "Borderline Hire":
        return "warning"
      default:
        return "destructive"
    }
  }

  // Format dynamic dates
  const formattedDate = session.started_at 
    ? new Date(session.started_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric"
      })
    : "Unknown Date"

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-7xl mx-auto select-text pb-12">
        {/* Top Breadcrumb/Nav */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild className="rounded-full">
            <Link href="/dashboard"><ArrowLeft className="h-5 w-5" /></Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight capitalize">
                {session.category.toLowerCase()} Mock Interview
              </h1>
              <Badge variant="secondary" className="capitalize">
                {session.role || "Backend"}
              </Badge>
            </div>
            <p className="text-muted-foreground text-sm flex items-center gap-2 mt-2">
              <Clock className="w-4 h-4" /> Completed on {formattedDate} • Difficulty: <span className="capitalize font-semibold">{session.difficulty.toLowerCase()}</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column - Score & Metrics */}
          <div className="space-y-6 md:col-span-1">
            <Card className="border border-border/60 shadow-sm bg-card">
              <CardHeader className="pb-4">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Overall Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center pt-2 pb-6">
                {/* Score circle utilizing direct SVG viewBox rendering for perfect centering and rounded corners */}
                <div className="relative w-36 h-36 flex items-center justify-center mb-6">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    {/* Background Circle track */}
                    <circle 
                      cx="50" 
                      cy="50" 
                      r="40" 
                      fill="transparent" 
                      stroke="hsl(var(--muted))" 
                      strokeWidth="8" 
                    />
                    {/* Active Progress Circle */}
                    <circle 
                      cx="50" 
                      cy="50" 
                      r="40" 
                      fill="transparent" 
                      stroke="hsl(var(--primary))" 
                      strokeWidth="8" 
                      strokeDasharray="251.2" 
                      strokeDashoffset={251.2 - (251.2 * evaluation.overall_score) / 100}
                      strokeLinecap="round"
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  {/* Absolute Centered Text inside Circle */}
                  <div className="absolute flex flex-col items-center">
                    <span className="text-4xl font-extrabold text-foreground">{evaluation.overall_score}</span>
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider mt-0.5">Score</span>
                  </div>
                </div>
                <Badge 
                  variant={getRecBadgeVariant(evaluation.recommendation)} 
                  className="text-sm px-4 py-1.5 font-bold tracking-wide shadow-sm"
                >
                  {evaluation.recommendation}
                </Badge>
              </CardContent>
            </Card>

            {/* Skill breakdown ratings */}
            <Card className="border border-border/60 shadow-sm bg-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold tracking-tight">Dimensions Rating</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 mt-4">
                {Object.entries(evaluation.skill_scores).map(([name, score]) => (
                  <div key={name} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-muted-foreground">{name}</span>
                      <div className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 fill-[#FBBC05] text-[#FBBC05]" />
                        <span className="font-bold text-foreground">{score.toFixed(1)}</span>
                      </div>
                    </div>
                    <Progress value={score * 20} className="h-1.5" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Tabs for Summary & Timeline */}
          <div className="md:col-span-2">
            <Card className="h-full border border-border/60 shadow-sm bg-card">
              <Tabs defaultValue="summary" className="w-full">
                <CardHeader className="border-b pb-4 pt-4 px-6 flex flex-row items-center justify-between bg-muted/20">
                  <TabsList className="bg-transparent h-10 p-0 space-x-2">
                    <TabsTrigger 
                      value="summary" 
                      className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-transparent rounded-full px-5 py-2 font-medium"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Overview
                    </TabsTrigger>
                    <TabsTrigger 
                      value="timeline" 
                      className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-transparent rounded-full px-5 py-2 font-medium"
                    >
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Timeline Reviews
                    </TabsTrigger>
                  </TabsList>
                </CardHeader>

                <CardContent className="p-6">
                  {/* 1. OVERVIEW SUMMARY TAB */}
                  <TabsContent value="summary" className="mt-0 space-y-6">
                    {evaluation.summary ? (
                      <div className="space-y-4">
                        <h3 className="font-semibold text-lg text-foreground tracking-tight">AI Evaluation Summary</h3>
                        <p className="text-muted-foreground text-base leading-relaxed select-text">
                          {evaluation.summary}
                        </p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                        <AlertCircle className="w-10 h-10 mb-2 opacity-50" />
                        <p className="text-sm">No summary is available for this report.</p>
                      </div>
                    )}
                  </TabsContent>

                  {/* 2. TIMELINE REVIEWS TAB */}
                  <TabsContent value="timeline" className="mt-0 space-y-6">
                    {evaluation.timeline_reviews.length > 0 ? (
                      <div className="space-y-4 max-h-[550px] overflow-y-auto pr-2">
                        {evaluation.timeline_reviews.map((item, idx) => {
                          const isExpanded = expandedIndex === idx
                          return (
                            <div 
                              key={idx} 
                              className="border border-border/80 rounded-xl overflow-hidden shadow-sm bg-card hover:border-primary/20 transition-all"
                            >
                              {/* Accordion Header */}
                              <button
                                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                                className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-muted/10 transition-colors"
                              >
                                <div className="flex items-center gap-3">
                                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">
                                    Q{idx + 1}
                                  </span>
                                  <div className="max-w-[340px] md:max-w-[480px] truncate font-semibold text-sm text-foreground">
                                    {item.question}
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                                    {item.score}/100
                                  </span>
                                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </div>
                              </button>

                              {/* Accordion Content */}
                              {isExpanded && (
                                <div className="px-5 pb-5 pt-3 border-t border-border/60 bg-muted/5 space-y-5 text-sm">
                                  {/* Question & Answer */}
                                  <div className="space-y-3">
                                    <div className="space-y-1">
                                      <div className="text-xs font-bold text-muted-foreground uppercase">Question:</div>
                                      <div className="text-foreground font-medium">{item.question}</div>
                                    </div>
                                    <div className="space-y-1">
                                      <div className="text-xs font-bold text-muted-foreground uppercase">Candidate Answer:</div>
                                      <div className="bg-muted/40 text-foreground p-3 rounded-lg border border-border/40 leading-relaxed italic">
                                        "{item.answer}"
                                      </div>
                                    </div>
                                  </div>

                                  {/* Critique Evaluation */}
                                  <div className="space-y-1 border-t border-border/40 pt-3">
                                    <div className="text-xs font-bold text-[#4285F4] uppercase">AI Feedback Critique:</div>
                                    <div className="text-muted-foreground leading-relaxed">{item.evaluation}</div>
                                  </div>

                                  {/* Ideal Reference Answer */}
                                  <div className="space-y-1 border-t border-border/40 pt-3">
                                    <div className="text-xs font-bold text-success uppercase">Ideal Reference Answer:</div>
                                    <div className="bg-[#34A853]/5 border border-[#34A853]/20 text-[#34A853]/90 p-3 rounded-lg leading-relaxed">
                                      {item.ideal_answer}
                                    </div>
                                  </div>

                                  {/* Strengths and Improvements Bullets */}
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-border/40 pt-3">
                                    {item.strengths.length > 0 && (
                                      <div className="space-y-1">
                                        <div className="text-xs font-bold text-success uppercase">Turn Strengths:</div>
                                        <ul className="list-disc pl-4 space-y-1 text-muted-foreground text-xs">
                                          {item.strengths.map((str, sIdx) => <li key={sIdx}>{str}</li>)}
                                        </ul>
                                      </div>
                                    )}
                                    {item.improvements.length > 0 && (
                                      <div className="space-y-1">
                                        <div className="text-xs font-bold text-warning uppercase">Areas for Improvement:</div>
                                        <ul className="list-disc pl-4 space-y-1 text-muted-foreground text-xs">
                                          {item.improvements.map((imp, iIdx) => <li key={iIdx}>{imp}</li>)}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                        <AlertCircle className="w-10 h-10 mb-2 opacity-50" />
                        <p className="text-sm">No timeline evaluations were generated for this session.</p>
                      </div>
                    )}
                  </TabsContent>
                </CardContent>
              </Tabs>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
