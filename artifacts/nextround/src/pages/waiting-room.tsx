import React, { useEffect, useState } from 'react';
import { useLocation, useParams } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Video, HelpCircle, User, FileText, Clock, PlayCircle, Loader2, RefreshCw } from 'lucide-react';

interface SessionDetail {
  id: string;
  category: string;
  role: string | null;
  difficulty: string;
  duration_minutes: number;
  status: string;
  resume_filename: string;
  blueprint_title: string | null;
}

export default function WaitingRoom() {
  const { id } = useParams<{ id: string }>();
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const token = useUserStore((state) => state.token);
  const refreshToken = useUserStore((state) => state.refreshToken);
  const isUserStoreLoading = useUserStore((state) => state.isLoading);

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Authenticated fetch wrapper
  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    let currentToken = token;
    
    const makeRequest = async (tokenVal: string | null) => {
      const headers = new Headers(options.headers || {});
      if (tokenVal) {
        headers.set('Authorization', `Bearer ${tokenVal}`);
      }
      return fetch(url, { ...options, headers });
    };

    let response = await makeRequest(currentToken);

    if (response.status === 401 && refreshToken) {
      try {
        const refreshRes = await fetch('http://localhost:8000/api/v1/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('refreshToken', data.refresh_token);
          useUserStore.setState({ token: data.access_token, refreshToken: data.refresh_token });
          
          response = await makeRequest(data.access_token);
        } else {
          localStorage.removeItem('profile');
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          useUserStore.setState({ profile: null, token: null, refreshToken: null, isAuthenticated: false });
        }
      } catch (err) {
        console.error("Token refresh failed:", err);
      }
    }

    return response;
  };

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Mock Interview Lobby']);
  }, [setBreadcrumbs]);

  const loadSessionDetails = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await fetchWithAuth(`http://localhost:8000/api/v1/interview/session/${id}`);
      if (!response.ok) {
        throw new Error("Unable to retrieve mock session details.");
      }
      const data = await response.json();
      setSession(data);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to load session details.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isUserStoreLoading) return;
    loadSessionDetails();
  }, [id, isUserStoreLoading, token]);

  const formatCategory = (cat: string) => {
    switch (cat) {
      case 'technical': return 'Technical Q&A';
      case 'coding': return 'Coding Challenge';
      case 'behavioral': return 'Behavioral Interview';
      case 'system_design': return 'System Design';
      default: return cat;
    }
  };

  const formatRole = (role: string | null) => {
    if (!role) return '';
    return role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8 select-none py-6 animate-fade-in">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground select-text">Mock Interview Lobby</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Test your device connections and review session constraints prior to initializing the AI coordinator.
          </p>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center p-16 bg-card border border-border/50 rounded-2xl">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
            <span className="text-xs font-semibold text-muted-foreground">Retrieving customized session configs...</span>
          </div>
        ) : errorMsg ? (
          <Card className="border border-red-500/15 bg-red-500/[0.01] p-8 rounded-2xl text-center space-y-4 max-w-md mx-auto">
            <div className="flex justify-center text-red-500">
              <HelpCircle className="h-10 w-10 animate-bounce" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-base font-bold text-foreground">Failed to Load Lobby</CardTitle>
              <CardDescription className="text-xs text-muted-foreground leading-relaxed">
                {errorMsg}
              </CardDescription>
            </div>
            <div className="pt-2">
              <Button
                onClick={loadSessionDetails}
                variant="outline"
                className="text-xs rounded-full gap-1 px-5"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry Connection
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            {/* Connection Video Preview Card */}
            <div className="lg:col-span-3 space-y-4">
              <div className="relative aspect-video rounded-3xl bg-black border border-border/80 flex items-center justify-center shadow-lg overflow-hidden group">
                <Video className="h-12 w-12 text-zinc-700 animate-pulse group-hover:text-zinc-500 transition-colors" />
                <span className="absolute bottom-4 left-4 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-[10px] font-bold text-white tracking-wide uppercase border border-white/10">
                  Lobby Camera Preview
                </span>
                
                {/* Visual Glass Mic Indicators */}
                <div className="absolute bottom-4 right-4 flex items-center gap-1 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 text-[10px] text-zinc-300">
                  <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping mr-1"></div>
                  Audio Calibrated
                </div>
              </div>
              <p className="text-[10px] text-muted-foreground leading-relaxed text-center px-4">
                Note: In this mock-interview, camera/voice stream remains private. No audio data leaves your device.
              </p>
            </div>

            {/* Session Summary Card */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="border border-border/60 bg-card/65 backdrop-blur-md rounded-3xl shadow-md overflow-hidden">
                <CardHeader className="pb-4 border-b border-border/40">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 uppercase tracking-wider select-text">
                      🟢 Ready
                    </span>
                    <span className="text-[9px] font-bold text-zinc-500 dark:text-zinc-400 bg-muted/40 px-2.5 py-0.5 rounded border border-border tracking-wider select-text">
                      Adaptive Difficulty
                    </span>
                  </div>
                  <CardTitle className="text-lg font-extrabold text-foreground pt-2 select-text">
                    {session?.blueprint_title || `${formatCategory(session?.category || '')} Session`}
                  </CardTitle>
                  {session?.role && (
                    <CardDescription className="text-xs font-semibold text-muted-foreground select-text">
                      Role Profile: {formatRole(session.role)}
                    </CardDescription>
                  )}
                </CardHeader>
                
                <CardContent className="p-6 space-y-5">
                  <div className="space-y-3.5 text-xs">
                    <div className="flex items-center justify-between text-muted-foreground select-text">
                      <span className="flex items-center gap-1.5 font-medium">
                        <Clock className="h-4 w-4 text-primary/75" />
                        Allocated Duration
                      </span>
                      <span className="font-bold text-foreground">{session?.duration_minutes} minutes</span>
                    </div>

                    <div className="flex items-center justify-between text-muted-foreground select-text">
                      <span className="flex items-center gap-1.5 font-medium">
                        <FileText className="h-4 w-4 text-primary/75" />
                        Target Resume
                      </span>
                      <span className="font-semibold text-foreground max-w-[150px] truncate" title={session?.resume_filename}>
                        {session?.resume_filename}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-muted-foreground select-text">
                      <span className="flex items-center gap-1.5 font-medium">
                        <User className="h-4 w-4 text-primary/75" />
                        Format
                      </span>
                      <span className="font-bold text-foreground">Interactive Q&A</span>
                    </div>
                  </div>

                  <div className="p-4 bg-muted/30 border border-border/80 rounded-2xl text-left space-y-1">
                    <h4 className="text-[11px] font-bold text-foreground">How it works:</h4>
                    <p className="text-[10px] text-muted-foreground leading-relaxed select-text">
                      The AI will initiate the discussion according to your profile blueprint. Focus on answering concisely. You will be evaluated across multiple competencies.
                    </p>
                  </div>

                  <div className="pt-2 border-t border-border/40">
                    <Button
                      disabled
                      className="w-full text-xs font-bold bg-[#4285F4] hover:bg-[#3b77db] text-white py-5 rounded-xl cursor-not-allowed opacity-50 flex items-center justify-center gap-1.5"
                    >
                      <PlayCircle className="h-4.5 w-4.5" />
                      Start Mock Interview
                    </Button>
                    <span className="block text-center text-[9px] text-amber-500 font-bold bg-amber-500/10 border border-amber-500/20 py-1.5 rounded-lg mt-2">
                      Waiting Room Active — Live interview execution unlocks in Phase 5.2
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
