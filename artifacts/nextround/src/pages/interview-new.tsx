import React, { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Code2, MessagesSquare, Laptop, Cpu, PlusCircle, AlertCircle, FileText, Sparkles, ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResumeListItem {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  is_primary: boolean;
}

export default function InterviewNew() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const token = useUserStore((state) => state.token);
  const refreshToken = useUserStore((state) => state.refreshToken);
  const isUserStoreLoading = useUserStore((state) => state.isLoading);

  const [resumesList, setResumesList] = useState<ResumeListItem[]>([]);
  const [isLoadingResumes, setIsLoadingResumes] = useState(true);
  
  // Form states
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<'technical' | 'coding' | 'behavioral' | 'system_design'>('technical');
  const [selectedRole, setSelectedRole] = useState<'backend' | 'frontend' | 'fullstack' | 'ai_ml' | 'data_science' | 'devops' | 'mobile'>('backend');
  
  const [isGenerating, setIsGenerating] = useState(false);
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
    setBreadcrumbs(['Dashboard', 'New Interview']);
  }, [setBreadcrumbs]);

  useEffect(() => {
    if (isUserStoreLoading) return;

    const loadResumes = async () => {
      try {
        const res = await fetchWithAuth('http://localhost:8000/api/v1/resume/list');
        if (res.ok) {
          const data: ResumeListItem[] = await res.json();
          // Filter to only confirmed resumes
          const confirmedResumes = data.filter((r) => r.status === 'confirmed');
          setResumesList(confirmedResumes);
          
          // Auto select primary or first confirmed resume
          if (confirmedResumes.length > 0) {
            const primary = confirmedResumes.find((r) => r.is_primary);
            setSelectedResumeId(primary ? primary.id : confirmedResumes[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to load resumes:", err);
      } finally {
        setIsLoadingResumes(false);
      }
    };

    loadResumes();
  }, [isUserStoreLoading, token]);

  const handleStart = async () => {
    if (!selectedResumeId) {
      setErrorMsg("Please select a confirmed resume first.");
      return;
    }
    
    setIsGenerating(true);
    setErrorMsg(null);

    try {
      const response = await fetchWithAuth('http://localhost:8000/api/v1/interview/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_id: selectedResumeId,
          category: selectedCategory,
          role: selectedCategory === 'technical' ? selectedRole : null,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to initialize interview session.");
      }

      const data = await response.json();
      setLocation(`/interviews/waiting-room/${data.session_id}`);
    } catch (err: any) {
      console.error("Failed to initialize session:", err);
      setErrorMsg(err.message || "An unexpected error occurred while setting up the interview.");
    } finally {
      setIsGenerating(false);
    }
  };

  const categories = [
    { id: 'technical', title: 'Technical Interview', desc: 'Questions covering your resume, technologies, and technical experiences.', icon: Cpu, color: '#4285F4' },
    { id: 'coding', title: 'Coding Challenge', desc: 'Interactive algorithms, data structures, and optimal coding patterns.', icon: Code2, color: '#34A853' },
    { id: 'behavioral', title: 'Behavioral prep', desc: 'Star methodology, team communication, leadership, and conflict resolution.', icon: MessagesSquare, color: '#FBBC05' },
    { id: 'system_design', title: 'System Design', desc: 'Scalable backends, high-availability architecture, caching, and CDN placement.', icon: Laptop, color: '#EA4335' },
  ] as const;

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto space-y-6 select-none relative pb-12">
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setLocation('/dashboard')}
            className="text-muted-foreground hover:text-foreground h-8 px-2.5 rounded-lg text-xs"
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </div>

        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground">Configure Mock Session</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Build your personalized agenda structure, customized entirely by AI based on your confirmed resume.
          </p>
        </div>

        {errorMsg && (
          <div className="p-4 bg-red-500/5 border border-red-500/15 text-red-500 rounded-2xl text-xs text-left flex items-start gap-2 animate-fade-in">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {isLoadingResumes ? (
          <Card className="border border-border/50 rounded-2xl p-12 text-center">
            <div className="flex justify-center mb-3">
              <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
            <span className="text-xs text-muted-foreground font-medium">Fetching candidate profiles...</span>
          </Card>
        ) : resumesList.length === 0 ? (
          <Card className="border border-border/50 rounded-2xl p-8 bg-card/65 backdrop-blur-md shadow-sm text-center space-y-4">
            <div className="flex justify-center">
              <div className="p-3.5 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-2xl">
                <AlertCircle className="h-8 w-8" />
              </div>
            </div>
            <div className="space-y-1.5 max-w-sm mx-auto">
              <CardTitle className="text-lg font-bold text-foreground">No Confirmed Resumes Found</CardTitle>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Before setting up an AI mock interview, you must upload and confirm a resume draft to generate candidate profile context.
              </p>
            </div>
            <div className="pt-2">
              <Button
                onClick={() => setLocation('/resume')}
                className="text-xs font-semibold bg-[#4285F4] hover:bg-[#3b77db] text-white rounded-full px-6"
              >
                Go to Resume Intelligence
              </Button>
            </div>
          </Card>
        ) : (
          <Card className="border border-border/50 rounded-2xl bg-card/65 backdrop-blur-md shadow-sm">
            <CardHeader className="p-6">
              <CardTitle className="text-lg">Interview Details</CardTitle>
              <CardDescription className="text-xs">Specify target resume and role profile alignment.</CardDescription>
            </CardHeader>
            
            <CardContent className="p-6 pt-0 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="resume-select" className="text-xs font-bold text-foreground">
                  Select Resume Profile
                </Label>
                <div className="relative">
                  <select
                    id="resume-select"
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="w-full h-11 text-xs rounded-xl px-4 pl-10 border border-border bg-background/50 hover:border-foreground/10 focus:border-primary/50 focus:outline-none transition-colors cursor-pointer"
                  >
                    {resumesList.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.filename} {r.is_primary ? '(Primary)' : ''}
                      </option>
                    ))}
                  </select>
                  <FileText className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground shrink-0" />
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-bold text-foreground">Select Category</Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {categories.map((cat) => {
                    const Icon = cat.icon;
                    const isSelected = selectedCategory === cat.id;
                    return (
                      <div
                        key={cat.id}
                        onClick={() => setSelectedCategory(cat.id)}
                        className={cn(
                          "p-5 rounded-2xl border border-border bg-card/50 hover:border-foreground/10 cursor-pointer transition-all duration-200 select-none flex flex-col justify-between h-36 relative overflow-hidden",
                          isSelected && "border-[#4285F4] ring-1 ring-[#4285F4] bg-[#4285F4]/[0.02]"
                        )}
                      >
                        <span className="absolute top-3.5 right-3.5 w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                        <div className="flex items-center">
                          <div 
                            className="p-2.5 rounded-xl border border-border/30 text-white shrink-0"
                            style={{ backgroundColor: cat.color }}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                        </div>
                        <div className="space-y-0.5 mt-2">
                          <h4 className="font-bold text-sm text-foreground leading-none">{cat.title}</h4>
                          <p className="text-[10px] text-muted-foreground leading-snug">{cat.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {selectedCategory === 'technical' && (
                <div className="space-y-2 animate-fade-in">
                  <Label htmlFor="role-select" className="text-xs font-bold text-foreground">
                    Target Technical Role
                  </Label>
                  <select
                    id="role-select"
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value as any)}
                    className="w-full h-11 text-xs rounded-xl px-4 border border-border bg-background/50 hover:border-foreground/10 focus:border-primary/50 focus:outline-none transition-colors cursor-pointer"
                  >
                    <option value="backend">Backend Engineer</option>
                    <option value="frontend">Frontend Engineer</option>
                    <option value="fullstack">Fullstack Engineer</option>
                    <option value="ai_ml">AI / Machine Learning Engineer</option>
                    <option value="data_science">Data Scientist</option>
                    <option value="devops">DevOps / Infrastructure Engineer</option>
                    <option value="mobile">Mobile (iOS / Android) Engineer</option>
                  </select>
                </div>
              )}
            </CardContent>

            <CardFooter className="p-6 border-t border-border/40 flex items-center justify-end">
              <Button
                onClick={handleStart}
                disabled={isGenerating}
                className="rounded-full gap-2 text-xs bg-[#4285F4] hover:bg-[#3b77db] text-white border-0 h-11 px-6 shadow-sm transition-colors font-bold"
              >
                {isGenerating ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Generating AI Blueprint...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 animate-pulse" />
                    Generate Session & Start
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
export { InterviewNew };
