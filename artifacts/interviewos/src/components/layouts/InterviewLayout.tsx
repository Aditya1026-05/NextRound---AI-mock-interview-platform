import React, { useEffect, useRef } from 'react';
import { useLocation } from 'wouter';
import { 
  Mic, 
  MicOff, 
  Play, 
  Terminal, 
  Clock, 
  ChevronRight, 
  LogOut, 
  MessageSquareText, 
  Settings, 
  Maximize2,
  Minimize2,
  BookOpenText,
  CodeSquare,
  Sparkles
} from 'lucide-react';
import { useInterviewStore } from '@/store/useInterviewStore';
import { useUIStore } from '@/store/useUIStore';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';

export function InterviewLayout({ children }: { children: React.ReactNode }) {
  const [, setLocation] = useLocation();
  const { 
    currentSession, 
    timerSeconds, 
    tickTimer, 
    isMuted, 
    toggleMute, 
    isListening, 
    setListening,
    endSession
  } = useInterviewStore();
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Tick timer while session is active
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentSession && currentSession.status !== 'completed') {
      interval = setInterval(() => {
        tickTimer();
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [currentSession, tickTimer]);

  // Format seconds -> MM:SS
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remaining = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remaining.toString().padStart(2, '0')}`;
  };

  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  const handleEndInterview = () => {
    endSession();
    setLocation('/dashboard');
  };

  if (!currentSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-6">
        <div className="max-w-md w-full text-center space-y-4">
          <h2 className="text-xl font-bold">No Active Interview Session</h2>
          <p className="text-muted-foreground text-sm">Please launch a new session from the dashboard.</p>
          <Button onClick={() => setLocation('/dashboard')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="min-h-screen bg-background text-foreground flex flex-col overflow-hidden select-none"
    >
      {/* Workspace Top Toolbar */}
      <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-card shrink-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 text-primary px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider">
            {currentSession.type}
          </div>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          <span className="font-semibold text-sm truncate max-w-[200px]">
            {currentSession.role} @ {currentSession.company}
          </span>
        </div>

        {/* Live Timer and Voice Actions */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-muted rounded-full text-xs font-mono border border-border">
            <Clock className="h-3.5 w-3.5 text-muted-foreground animate-pulse" />
            <span>{formatTime(timerSeconds)}</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={isMuted ? 'destructive' : 'outline'}
              size="icon"
              className="h-8 w-8 rounded-full"
              onClick={toggleMute}
              title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
            >
              {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>

            <Button
              variant={isListening ? 'default' : 'outline'}
              size="sm"
              className={cn("h-8 rounded-full text-xs gap-1.5", isListening && "bg-emerald-600 hover:bg-emerald-700 text-white")}
              onClick={() => setListening(!isListening)}
            >
              <span className={cn("w-2 h-2 rounded-full", isListening ? "bg-white animate-ping" : "bg-muted-foreground")} />
              {isListening ? 'AI Listening' : 'Talk to AI'}
            </Button>
          </div>
        </div>

        {/* Workspace Windows Operations */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={handleToggleFullscreen}>
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>

          <Button 
            variant="destructive" 
            size="sm" 
            className="h-8 rounded-md text-xs font-medium" 
            onClick={handleEndInterview}
          >
            <LogOut className="h-3.5 w-3.5 mr-1" />
            End Session
          </Button>
        </div>
      </header>

      {/* Main Resizable Panels Content Area */}
      <div className="flex-1 min-h-0 bg-background">
        {children}
      </div>
    </div>
  );
}
