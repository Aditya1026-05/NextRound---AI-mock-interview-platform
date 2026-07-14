import * as React from "react"
import { useLocation, Link } from "wouter"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowRight, Check, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

export default function Auth() {
  const [location, setLocation] = useLocation()
  const isSignUp = location === "/signup"

  const handleToggle = (signup: boolean) => {
    setLocation(signup ? "/signup" : "/login")
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock login/signup, redirect to dashboard
    setLocation("/dashboard")
  }

  return (
    <div
      className="min-h-[100dvh] flex flex-col text-foreground relative z-0 overflow-hidden bg-background"
      style={{
        backgroundImage:
          "radial-gradient(120% 90% at 15% 0%, rgba(66,133,244,0.10), transparent 60%), radial-gradient(90% 70% at 100% 15%, rgba(251,188,5,0.08), transparent 55%), radial-gradient(80% 60% at 85% 100%, rgba(234,67,53,0.05), transparent 60%), radial-gradient(70% 60% at 0% 100%, rgba(52,168,83,0.05), transparent 55%)",
      }}
    >
      {/* Subtle Background Gradient (dark mode overrides + soft blur accents) */}
      <div className="absolute inset-0 pointer-events-none -z-10 hidden dark:block"
        style={{
          backgroundImage:
            "radial-gradient(120% 90% at 15% 0%, rgba(66,133,244,0.16), transparent 60%), radial-gradient(90% 70% at 100% 15%, rgba(251,188,5,0.07), transparent 55%), radial-gradient(80% 60% at 85% 100%, rgba(234,67,53,0.06), transparent 60%), radial-gradient(70% 60% at 0% 100%, rgba(52,168,83,0.06), transparent 55%)",
        }}
      />
      <div className="absolute inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-[#4285F4]/[0.08] dark:bg-[#4285F4]/[0.15] blur-[120px]" />
        <div className="absolute bottom-[10%] right-[-5%] w-[40vw] h-[40vw] rounded-full bg-[#FBBC05]/[0.04] dark:bg-[#FBBC05]/[0.06] blur-[100px]" />
      </div>

      {/* Top Bar */}
      <header className="h-20 px-6 md:px-12 flex items-center justify-between shrink-0">
        <Link href="/" className="flex items-center gap-3 cursor-pointer">
          <div className="bg-primary text-primary-foreground w-8 h-8 rounded-full flex items-center justify-center font-bold shadow-sm">
            IO
          </div>
          <span className="font-bold text-xl tracking-tight flex items-center gap-1.5">
            InterviewOS
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Button variant="outline" className="hidden sm:flex rounded-full px-6" asChild>
            <Link href="/">Back to home</Link>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row items-center justify-center max-w-[1200px] w-full mx-auto p-6 md:p-12 gap-12 lg:gap-24">
        
        {/* Left Side: Hero Copy */}
        <div className="flex-1 max-w-xl text-center lg:text-left space-y-6 flex flex-col items-center lg:items-start">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-background/50 border shadow-sm text-sm font-medium mb-2 text-foreground backdrop-blur-md"
          >
            <div className="w-6 h-6 rounded-full bg-[#4285F4]/10 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-[#4285F4]" />
            </div>
            <span>Meet your new AI interviewer</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="flex flex-col gap-2 md:gap-3"
          >
            <span className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
              Practice smarter with
            </span>
            <span className="text-5xl md:text-7xl font-black tracking-tighter leading-[1.05] text-[#4285F4]">
              AI-powered<br />mock interviews
            </span>
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-xl text-muted-foreground"
          >
            Nail your next behavioral or technical round. Real-time feedback, personalized questions, and zero judgment.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="hidden lg:block space-y-4 pt-4"
          >
            {[
              "System Design & Coding algorithms",
              "Behavioral & cultural fit",
              "Instant AI analysis and scoring"
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-3 text-muted-foreground">
                <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <Check className="w-3 h-3 text-primary" />
                </div>
                <span className="font-medium text-foreground">{feature}</span>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Right Side: Auth Form */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="w-full max-w-md shrink-0"
        >
          <Card className="border shadow-lg rounded-2xl overflow-hidden bg-card">
            <CardContent className="p-6 md:p-8 space-y-8">
              
              {/* Segmented Toggle */}
              <div className="bg-secondary/50 p-1 rounded-full flex relative">
                <button
                  type="button"
                  onClick={() => handleToggle(false)}
                  className={cn(
                    "flex-1 py-2.5 text-sm font-semibold rounded-full transition-colors relative z-10",
                    !isSignUp ? "text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  Log in
                </button>
                <button
                  type="button"
                  onClick={() => handleToggle(true)}
                  className={cn(
                    "flex-1 py-2.5 text-sm font-semibold rounded-full transition-colors relative z-10",
                    isSignUp ? "text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  Sign up
                </button>
                {/* Active Slider */}
                <motion.div
                  className="absolute top-1 bottom-1 w-[calc(50%-4px)] bg-primary/10 rounded-full"
                  initial={false}
                  animate={{ 
                    x: isSignUp ? "100%" : "0%",
                    left: isSignUp ? "4px" : "4px" 
                  }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <AnimatePresence mode="popLayout" initial={false}>
                  {isSignUp && (
                    <motion.div
                      key="name-fields"
                      initial={{ opacity: 0, height: 0, y: -10 }}
                      animate={{ opacity: 1, height: "auto", y: 0 }}
                      exit={{ opacity: 0, height: 0, y: -10 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-4 overflow-hidden"
                    >
                      <div className="space-y-2">
                        <Label htmlFor="name">Full Name</Label>
                        <Input 
                          id="name" 
                          placeholder="John Doe" 
                          required={isSignUp}
                          className="rounded-full bg-secondary h-11 px-4 border-transparent focus:border-primary focus:bg-background transition-colors"
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    placeholder="you@example.com" 
                    required
                    className="rounded-full bg-secondary h-11 px-4 border-transparent focus:border-primary focus:bg-background transition-colors"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    {!isSignUp && (
                      <Link href="/login" className="text-xs text-primary font-medium hover:underline">
                        Forgot password?
                      </Link>
                    )}
                  </div>
                  <Input 
                    id="password" 
                    type="password" 
                    required
                    className="rounded-full bg-secondary h-11 px-4 border-transparent focus:border-primary focus:bg-background transition-colors"
                  />
                </div>

                <AnimatePresence mode="popLayout" initial={false}>
                  {isSignUp && (
                    <motion.div
                      key="confirm-password"
                      initial={{ opacity: 0, height: 0, y: -10 }}
                      animate={{ opacity: 1, height: "auto", y: 0 }}
                      exit={{ opacity: 0, height: 0, y: -10 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-2 overflow-hidden"
                    >
                      <Label htmlFor="confirm-password">Confirm Password</Label>
                      <Input 
                        id="confirm-password" 
                        type="password" 
                        required={isSignUp}
                        className="rounded-full bg-secondary h-11 px-4 border-transparent focus:border-primary focus:bg-background transition-colors"
                      />
                    </motion.div>
                  )}
                </AnimatePresence>

                <Button type="submit" className="w-full rounded-full h-11 mt-6 text-base font-medium shadow-md bg-gradient-to-r from-[#4285F4] to-[#2b68ce] text-white hover:opacity-90 border-0 transition-opacity">
                  {isSignUp ? "Create account" : "Log in"}
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground font-medium">
                    Or continue with
                  </span>
                </div>
              </div>

              <Button type="button" variant="outline" className="w-full rounded-full h-11 gap-2 font-medium bg-background hover:bg-secondary">
                <GoogleIcon />
                Continue with Google
              </Button>

              <p className="text-center text-sm text-muted-foreground pt-2">
                {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
                <button 
                  type="button"
                  onClick={() => handleToggle(!isSignUp)}
                  className="text-[#4285F4] font-semibold hover:underline cursor-pointer"
                >
                  {isSignUp ? "Log in" : "Sign up"}
                </button>
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  )
}
