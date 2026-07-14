import { AlertCircle } from "lucide-react"
import { Link } from "wouter"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-background text-foreground space-y-6 p-8 min-h-[60vh]">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted/50 mb-4">
        <AlertCircle className="h-10 w-10 text-muted-foreground" strokeWidth={1.5} />
      </div>
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">404</h1>
        <p className="text-lg text-muted-foreground">The page you're looking for doesn't exist.</p>
      </div>
      <Button asChild>
        <Link href="/dashboard">Return to Dashboard</Link>
      </Button>
    </div>
  )
}
