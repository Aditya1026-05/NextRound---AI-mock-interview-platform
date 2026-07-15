import React from 'react';
import { Sparkles } from 'lucide-react';

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 text-foreground relative select-none">
      {/* Decorative premium blurs */}
      <div className="absolute top-[10%] left-[20%] w-[400px] h-[400px] rounded-full bg-violet-500/5 dark:bg-violet-500/10 blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-[10%] right-[20%] w-[350px] h-[350px] rounded-full bg-indigo-500/5 dark:bg-indigo-500/10 blur-[100px] pointer-events-none -z-10" />

      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="bg-foreground text-background w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg shadow-sm">
            io
          </div>
          <h1 className="text-2xl font-bold tracking-tight">InterviewOS</h1>
          <p className="text-xs text-muted-foreground max-w-xs">
            The AI-powered interview operating system for engineering teams and candidates.
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-card border border-border rounded-xl p-6 md:p-8 shadow-sm">
          {children}
        </div>

        {/* Footer info */}
        <div className="text-center text-[10px] text-muted-foreground flex items-center justify-center gap-1">
          <Sparkles className="h-3 w-3 text-violet-500 animate-pulse" />
          <span>Calm, intelligent, and engineering-focused preparation.</span>
        </div>
      </div>
    </div>
  );
}
