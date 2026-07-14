import * as React from "react"
import { Search, Filter, Play } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/empty-state"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const MOCK_QUESTIONS = [
  { id: 1, title: "Design Twitter / X", category: "System Design", difficulty: "Hard", status: "Completed", company: "Twitter" },
  { id: 2, title: "Implement a Rate Limiter", category: "System Design", difficulty: "Medium", status: "Attempted", company: "Stripe" },
  { id: 3, title: "Two Sum", category: "Coding", difficulty: "Easy", status: "Completed", company: "Google" },
  { id: 4, title: "Tell me about a time you failed", category: "Behavioral", difficulty: "Medium", status: "Not Started", company: "General" },
  { id: 5, title: "Gradient Descent Implementation", category: "Machine Learning", difficulty: "Hard", status: "Not Started", company: "OpenAI" },
  { id: 6, title: "LRU Cache", category: "Coding", difficulty: "Medium", status: "Not Started", company: "Amazon" },
]

export default function Practice() {
  const [loading, setLoading] = React.useState(true)
  const [search, setSearch] = React.useState("")
  const [filter, setFilter] = React.useState("all")

  // Simulate network loading
  React.useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(timer)
  }, [])

  const filteredQuestions = MOCK_QUESTIONS.filter((q) => {
    const matchesSearch = q.title.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === "all" || q.category.toLowerCase() === filter.toLowerCase()
    return matchesSearch && matchesFilter
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Practice Library</h1>
        <p className="text-muted-foreground mt-1">Explore questions across all disciplines to prepare effectively.</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-card p-4 rounded-xl border">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search questions..." 
            className="pl-9 bg-background"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-[180px]">
              <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="system design">System Design</SelectItem>
              <SelectItem value="coding">Coding</SelectItem>
              <SelectItem value="behavioral">Behavioral</SelectItem>
              <SelectItem value="machine learning">Machine Learning</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="hidden sm:flex">Shuffle</Button>
        </div>
      </div>

      <div className="space-y-4">
        {loading ? (
          // Loading Skeletons
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex items-center p-4 gap-4">
                  <Skeleton className="h-12 w-12 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-1/3" />
                    <Skeleton className="h-4 w-1/4" />
                  </div>
                  <Skeleton className="h-8 w-24 rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))
        ) : filteredQuestions.length === 0 ? (
          // Empty State
          <EmptyState 
            title="No questions found" 
            description="We couldn't find any questions matching your filters. Try adjusting your search."
            action={{ label: "Clear Filters", onClick: () => { setSearch(""); setFilter("all") } }}
          />
        ) : (
          // Actual List
          filteredQuestions.map((q) => (
            <Card key={q.id} className="group cursor-pointer hover:border-primary/50">
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{q.title}</h3>
                    {q.company !== "General" && (
                      <span className="text-xs font-medium px-2 py-1 bg-secondary rounded-md text-secondary-foreground">
                        {q.company}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">{q.category}</span>
                    <span>•</span>
                    <span className={
                      q.difficulty === "Hard" ? "text-destructive" :
                      q.difficulty === "Medium" ? "text-warning" : "text-success"
                    }>{q.difficulty}</span>
                    <span>•</span>
                    <span>{q.status}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 w-full sm:w-auto mt-4 sm:mt-0">
                  <Button variant={q.status === "Completed" ? "outline" : "default"} className="w-full sm:w-auto gap-2 group-hover:shadow-md transition-shadow">
                    <Play className="w-4 h-4" />
                    {q.status === "Completed" ? "Review" : "Start"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
