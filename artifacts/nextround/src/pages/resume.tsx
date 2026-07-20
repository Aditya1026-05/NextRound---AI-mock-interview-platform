import React, { useEffect, useState, useRef } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { 
  FileUp, 
  Sparkles, 
  CheckCircle2, 
  Trash2, 
  Plus, 
  BookOpen, 
  Briefcase, 
  Wrench, 
  Award, 
  Info,
  Calendar,
  AlertCircle
} from 'lucide-react';

interface ParsedEducation {
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string | null;
  end_date: string | null;
  gpa: number | null;
  confidence?: number;
}

interface ParsedWorkExperience {
  company: string;
  role: string;
  location: string | null;
  description: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  confidence?: number;
}

interface ParsedProject {
  title: string;
  description: string;
  role: string | null;
  url: string | null;
  confidence?: number;
}

interface ParsedSkill {
  name: string;
  confidence?: number;
}

interface ParsedResume {
  resume_id: string;
  status: string;
  full_name: string;
  summary: string;
  education: ParsedEducation[];
  work_experiences: ParsedWorkExperience[];
  projects: ParsedProject[];
  skills: ParsedSkill[];
  certifications: string[];
  achievements: string[];
  confidence_score: number | null;
  parser_provider: string;
  parser_model: string;
  parser_version: string | null;
}

const STAGES = [
  "Uploading resume...",
  "✓ Upload complete",
  "Extracting text...",
  "Analyzing resume...",
  "Preparing your profile..."
];

export default function ResumeIntelligence() {
  const { setBreadcrumbs } = useUIStore();
  const token = useUserStore((state) => state.token);
  const refreshToken = useUserStore((state) => state.refreshToken);
  
  const [fileName, setFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // Parsed Resume data state
  const [parsedData, setParsedData] = useState<ParsedResume | null>(null);
  const [activeTab, setActiveTab] = useState<'experience' | 'education' | 'projects' | 'skills'>('experience');

  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const isUserStoreLoading = useUserStore((state) => state.isLoading);
  const [resumesList, setResumesList] = useState<any[]>([]);
  const [resumeTitle, setResumeTitle] = useState("");
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [draftSavedMessage, setDraftSavedMessage] = useState<string | null>(null);

  const [, setLocation] = useLocation();
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [confirmStage, setConfirmStage] = useState(0);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [isConfirmedSuccess, setIsConfirmedSuccess] = useState(false);

  // Authenticated fetch wrapper that automatically handles token refreshes on 401
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
      console.warn("Access token expired. Attempting token refresh...");
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
          console.error("Refresh token expired. Logging out...");
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
    if (isUserStoreLoading) return; // Wait until token initialization completes

    setBreadcrumbs(['Dashboard', 'Resume Intelligence']);

    const initResumeData = async () => {
      if (!token) {
        setIsLoadingProfile(false);
        return;
      }
      try {
        // 1. Fetch resumes list
        const listRes = await fetchWithAuth('http://localhost:8000/api/v1/resume/list');
        let listData = [];
        if (listRes.ok) {
          listData = await listRes.json();
          setResumesList(listData);
        }

        // 2. Fetch latest parsed resume
        const response = await fetchWithAuth('http://localhost:8000/api/v1/resume');
        if (response.ok) {
          const data = await response.json();
          if (data && data.resume_id) {
            setParsedData(data);
            const matched = listData.find((r: any) => r.id === data.resume_id);
            setResumeTitle(matched?.filename || "My Resume Profile");
          }
        }
      } catch (err) {
        console.error('Failed to load candidate resume data:', err);
      } finally {
        setIsLoadingProfile(false);
      }
    };

    initResumeData();
  }, [setBreadcrumbs, token, isUserStoreLoading]);

  // Timed stage simulation wrapper
  const stageInterval = useRef<NodeJS.Timeout | null>(null);

  const simulateStages = (completionPromise: Promise<any>) => {
    setCurrentStage(0);
    setIsUploading(true);
    setUploadError(null);

    // Fast-forward interval every 900ms
    stageInterval.current = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < STAGES.length - 2) {
          return prev + 1;
        }
        return prev; // Hold at "Analyzing resume..." until promise resolves
      });
    }, 900);

    completionPromise
      .then((data) => {
        // Fast-forward to final stage, then transition
        setCurrentStage(STAGES.length - 1);
        setTimeout(async () => {
          setIsUploading(false);
          setParsedData(data);
          setResumeTitle(data.original_filename || "My Resume Profile");
          if (stageInterval.current) clearInterval(stageInterval.current);

          // Re-fetch resumes list
          try {
            const listRes = await fetchWithAuth('http://localhost:8000/api/v1/resume/list');
            if (listRes.ok) {
              setResumesList(await listRes.json());
            }
          } catch (e) {
            console.error(e);
          }
        }, 800);
      })
      .catch((err) => {
        setIsUploading(false);
        setUploadError(err.message || "An error occurred during parsing.");
        if (stageInterval.current) clearInterval(stageInterval.current);
      });
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    const apiCall = async () => {
      const response = await fetchWithAuth('http://localhost:8000/api/v1/resume/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to process resume.");
      }

      return response.json();
    };

    simulateStages(apiCall());
  };

  // State handlers for editable sections
  const handleMetaChange = (field: keyof ParsedResume, value: any) => {
    if (!parsedData) return;
    setParsedData({ ...parsedData, [field]: value });
  };

  const handleEduChange = (index: number, field: keyof ParsedEducation, value: any) => {
    if (!parsedData) return;
    const newEdu = [...parsedData.education];
    newEdu[index] = { ...newEdu[index], [field]: value };
    setParsedData({ ...parsedData, education: newEdu });
  };

  const addEducation = () => {
    if (!parsedData) return;
    const newEdu: ParsedEducation = {
      institution: '',
      degree: '',
      field_of_study: '',
      start_date: '',
      end_date: '',
      gpa: null,
      confidence: 1.0
    };
    setParsedData({ ...parsedData, education: [...parsedData.education, newEdu] });
  };

  const removeEducation = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      education: parsedData.education.filter((_, i) => i !== index)
    });
  };

  const handleExpChange = (index: number, field: keyof ParsedWorkExperience, value: any) => {
    if (!parsedData) return;
    const newExp = [...parsedData.work_experiences];
    newExp[index] = { ...newExp[index], [field]: value };
    setParsedData({ ...parsedData, work_experiences: newExp });
  };

  const addExperience = () => {
    if (!parsedData) return;
    const newExp: ParsedWorkExperience = {
      company: '',
      role: '',
      location: '',
      description: '',
      start_date: '',
      end_date: '',
      is_current: false,
      confidence: 1.0
    };
    setParsedData({ ...parsedData, work_experiences: [...parsedData.work_experiences, newExp] });
  };

  const removeExperience = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      work_experiences: parsedData.work_experiences.filter((_, i) => i !== index)
    });
  };

  const handleProjectChange = (index: number, field: keyof ParsedProject, value: any) => {
    if (!parsedData) return;
    const newProj = [...parsedData.projects];
    newProj[index] = { ...newProj[index], [field]: value };
    setParsedData({ ...parsedData, projects: newProj });
  };

  const addProject = () => {
    if (!parsedData) return;
    const newProj: ParsedProject = {
      title: '',
      description: '',
      role: '',
      url: '',
      confidence: 1.0
    };
    setParsedData({ ...parsedData, projects: [...parsedData.projects, newProj] });
  };

  const removeProject = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      projects: parsedData.projects.filter((_, i) => i !== index)
    });
  };

  const removeSkill = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      skills: parsedData.skills.filter((_, i) => i !== index)
    });
  };

  const addSkill = (name: string) => {
    if (!parsedData || !name.trim()) return;
    if (parsedData.skills.some(s => s.name.toLowerCase() === name.toLowerCase())) return;
    setParsedData({
      ...parsedData,
      skills: [...parsedData.skills, { name: name.trim(), confidence: 1.0 }]
    });
  };

  const removeCert = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      certifications: parsedData.certifications.filter((_, i) => i !== index)
    });
  };

  const addCert = (name: string) => {
    if (!parsedData || !name.trim()) return;
    setParsedData({
      ...parsedData,
      certifications: [...parsedData.certifications, name.trim()]
    });
  };

  const removeAchievement = (index: number) => {
    if (!parsedData) return;
    setParsedData({
      ...parsedData,
      achievements: parsedData.achievements.filter((_, i) => i !== index)
    });
  };

  const addAchievement = (name: string) => {
    if (!parsedData || !name.trim()) return;
    setParsedData({
      ...parsedData,
      achievements: [...parsedData.achievements, name.trim()]
    });
  };

  const handleFillManually = async () => {
    setIsLoadingProfile(true);
    try {
      const res = await fetchWithAuth('http://localhost:8000/api/v1/resume/manual', {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setParsedData(data);
        setResumeTitle(data.original_filename || "New Manual Profile");
        
        // Re-fetch resumes list
        const listRes = await fetchWithAuth('http://localhost:8000/api/v1/resume/list');
        if (listRes.ok) {
          setResumesList(await listRes.json());
        }
      }
    } catch (err) {
      console.error('Failed to initialize manual resume:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!parsedData?.resume_id || parsedData.resume_id === 'new') return;
    setIsSavingDraft(true);
    setDraftSavedMessage(null);
    try {
      const res = await fetchWithAuth(`http://localhost:8000/api/v1/resume/${parsedData.resume_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(parsedData),
      });
      if (res.ok) {
        const data = await res.json();
        setParsedData(data);
        setDraftSavedMessage("Draft saved successfully!");
        setTimeout(() => setDraftSavedMessage(null), 3000);
      } else {
        setDraftSavedMessage("Failed to save draft.");
      }
    } catch (err) {
      console.error('Failed to save draft:', err);
      setDraftSavedMessage("Failed to save draft.");
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handleLoadResume = async (resumeId: string) => {
    if (!resumeId) {
      setParsedData(null);
      setResumeTitle("");
      return;
    }
    setIsLoadingProfile(true);
    try {
      const res = await fetchWithAuth(`http://localhost:8000/api/v1/resume/${resumeId}`);
      if (res.ok) {
        const data = await res.json();
        setParsedData(data);
        const matched = resumesList.find(r => r.id === resumeId);
        setResumeTitle(matched?.filename || "My Resume Profile");
      }
    } catch (err) {
      console.error('Failed to load selected resume:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const handleRenameResume = async () => {
    if (!parsedData?.resume_id || parsedData.resume_id === 'new' || !resumeTitle.trim()) return;
    try {
      const res = await fetchWithAuth(`http://localhost:8000/api/v1/resume/${parsedData.resume_id}/rename`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: resumeTitle.trim() }),
      });
      if (res.ok) {
        const updated = await res.json();
        // Update resumes list cache
        setResumesList(prev => prev.map(r => r.id === updated.id ? updated : r));
      }
    } catch (err) {
      console.error('Failed to rename resume:', err);
    }
  };

  const handleDeleteResume = async () => {
    if (!parsedData?.resume_id || parsedData.resume_id === 'new') return;
    if (!window.confirm("Are you sure you want to delete this resume profile? This cannot be undone.")) return;

    try {
      const res = await fetchWithAuth(`http://localhost:8000/api/v1/resume/${parsedData.resume_id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setParsedData(null);
        setFileName(null);
        setResumeTitle("");
        // Update resumes list cache
        setResumesList(prev => prev.filter(r => r.id !== parsedData.resume_id));
      }
    } catch (err) {
      console.error('Failed to delete resume:', err);
    }
  };

  const handleConfirmResume = async () => {
    if (!parsedData?.resume_id || parsedData.resume_id === 'new') return;
    
    setShowConfirmModal(false);
    setIsConfirming(true);
    setConfirmStage(0);
    setConfirmError(null);

    const stageTimer1 = setTimeout(() => setConfirmStage(1), 1000); // Saving Resume
    const stageTimer2 = setTimeout(() => setConfirmStage(2), 2200); // Preparing Profile
    const stageTimer3 = setTimeout(() => setConfirmStage(3), 4500); // Finalizing

    try {
      const response = await fetchWithAuth(`http://localhost:8000/api/v1/resume/${parsedData.resume_id}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(parsedData),
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Confirmation request failed.");
      }

      setConfirmStage(3);
      setTimeout(() => {
        setIsConfirming(false);
        setIsConfirmedSuccess(true);
      }, 500);

    } catch (err: any) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      console.error("Confirmation error:", err);
      setConfirmError(err.message || "An unexpected error occurred during confirmation.");
      setIsConfirming(false);
    }
  };

  if (isLoadingProfile) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <span className="text-xs text-muted-foreground animate-pulse font-medium">Loading candidate profile...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (isConfirming) {
    const CONFIRM_STAGES = [
      "Validating Resume...",
      "Saving Resume...",
      "Preparing Interview Profile...",
      "Finalizing..."
    ];
    return (
      <DashboardLayout>
        <div className="max-w-md mx-auto my-16 text-center space-y-6 animate-pulse select-none">
          <div className="flex justify-center">
            <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-foreground">Processing Confirmation</h3>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto">
              Please wait while we normalize your resume entries and generate candidate intelligence.
            </p>
          </div>
          <div className="max-w-xs mx-auto bg-muted/20 border border-border/60 rounded-xl p-4 text-left space-y-2">
            {CONFIRM_STAGES.map((stg, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                {confirmStage > idx ? (
                  <span className="text-emerald-500 font-bold">✓</span>
                ) : confirmStage === idx ? (
                  <span className="text-primary animate-spin">⏳</span>
                ) : (
                  <span className="text-muted-foreground/30">•</span>
                )}
                <span className={confirmStage === idx ? "font-bold text-foreground" : "text-muted-foreground"}>
                  {stg}
                </span>
              </div>
            ))}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (isConfirmedSuccess) {
    return (
      <DashboardLayout>
        <div className="max-w-md mx-auto my-12 animate-fade-in select-none">
          <Card className="border border-border shadow-md">
            <CardHeader className="text-center pb-4">
              <div className="flex justify-center mb-3">
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-full">
                  <CheckCircle2 className="h-10 w-10" />
                </div>
              </div>
              <CardTitle className="text-2xl font-extrabold text-foreground">Resume Confirmed</CardTitle>
              <CardDescription className="text-xs text-muted-foreground mt-1">
                Your technical candidate profile has been generated and finalized.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-center">
              <p className="text-xs text-muted-foreground leading-relaxed">
                This resume is now set as your primary profile and will be used as the source of truth to customize your future mock interview sessions.
              </p>
              
              <div className="flex flex-col gap-2 pt-2">
                <Button 
                  onClick={() => setLocation('/dashboard')}
                  className="w-full text-xs font-bold bg-primary hover:bg-primary/90 text-primary-foreground"
                >
                  Return to Dashboard
                </Button>
                <div className="flex items-center justify-center gap-1.5 pt-1">
                  <Button 
                    disabled 
                    variant="outline" 
                    className="w-full text-xs font-bold text-muted-foreground cursor-not-allowed opacity-50 flex items-center justify-center gap-1"
                  >
                    Start Interview
                  </Button>
                  <span className="text-[9px] font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 whitespace-nowrap">
                    Available in Phase 5
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6 select-none pb-12 animate-fade-in">
        {/* Header Block */}
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
            Resume Intelligence
          </h2>
          <p className="text-muted-foreground text-sm mt-1">
            Analyze your CV with deep AI matching algorithms to evaluate strength, find omissions, and generate custom target interview templates.
          </p>
          <div className="mt-2 bg-muted/20 border border-border rounded-lg p-2.5 flex items-center gap-2 text-xs text-muted-foreground">
            <Info className="h-4 w-4 text-amber-500 shrink-0" />
            <span>
              <strong>Note:</strong> If you have any links (e.g. projects, portfolios, or social profiles), please add them manually under the relevant tabs.
            </span>
          </div>
          {resumesList.length > 0 && (
            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs bg-muted/20 border border-border p-3 rounded-xl">
              <span className="font-semibold text-muted-foreground">My Saved Profiles:</span>
              <select
                value={parsedData?.resume_id || ""}
                onChange={(e) => handleLoadResume(e.target.value)}
                className="bg-background border border-border rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-ring text-xs max-w-xs cursor-pointer"
              >
                <option value="">-- Start a new profile --</option>
                {resumesList.map((res) => (
                  <option key={res.id} value={res.id}>
                    {res.filename} ({new Date(res.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Upload Mode Screen */}
        {!isUploading && !parsedData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 bg-card border border-border shadow-sm">
              <CardHeader className="p-6">
                <CardTitle className="text-base font-bold">Upload Resume</CardTitle>
                <CardDescription className="text-xs">Upload your PDF or Word document to parse capabilities.</CardDescription>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                <div className="border border-dashed border-border rounded-xl p-10 text-center bg-muted/50 flex flex-col items-center justify-center space-y-4">
                  <div className="p-3.5 rounded-full bg-background text-foreground shrink-0 border border-border shadow-sm">
                    <FileUp className="h-6 w-6 text-foreground/80" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold">Drag & drop your file here, or click to browse</p>
                    <p className="text-[10px] text-muted-foreground">PDF, DOCX up to 10MB</p>
                  </div>
                  <Input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleUpload}
                    className="hidden"
                    id="resume-input"
                  />
                  <div className="flex flex-wrap justify-center gap-3">
                    <Button 
                      asChild 
                      variant="outline" 
                      size="sm" 
                      className="rounded-full text-xs font-semibold px-6"
                    >
                      <label htmlFor="resume-input" className="cursor-pointer">
                        Select File
                      </label>
                    </Button>
                    <Button 
                      onClick={handleFillManually}
                      variant="ghost" 
                      size="sm" 
                      className="rounded-full text-xs font-semibold px-6 border border-border"
                    >
                      Fill Manually
                    </Button>
                  </div>
                </div>

                {uploadError && (
                  <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-lg flex items-center gap-2 font-medium">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-card border border-border shadow-sm flex flex-col justify-between">
              <CardHeader className="p-6">
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <Sparkles className="h-4.5 w-4.5 text-violet-500" />
                  AI Parser Engine
                </CardTitle>
                <CardDescription className="text-xs">Extracted resume insights.</CardDescription>
              </CardHeader>
              <CardContent className="p-6 pt-0 space-y-4 text-xs">
                <div className="space-y-1">
                  <p className="font-semibold text-muted-foreground">Primary Focus</p>
                  <p className="font-bold text-foreground text-xs">Structured normalization of projects, skills, education, and experiences.</p>
                </div>
                <div className="space-y-1">
                  <p className="font-semibold text-muted-foreground">Model Engine</p>
                  <p className="font-bold text-foreground">Gemini 2.5 Flash</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Granular Parsing Stages Animation Screen */}
        {isUploading && (
          <Card className="p-10 text-center bg-card border border-border shadow-sm flex flex-col items-center justify-center space-y-6 py-16">
            <div className="relative flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-violet-500 animate-pulse relative z-10" />
            </div>

            <div className="space-y-2 max-w-md w-full">
              <h3 className="text-base font-bold tracking-tight">Analyzing your resume...</h3>
              <p className="text-xs text-muted-foreground">Please wait while Gemini processes the document structures.</p>
            </div>

            {/* Stages Progression indicator */}
            <div className="w-full max-w-sm space-y-3.5 pt-4 text-left">
              {STAGES.map((stage, idx) => {
                const isCompleted = idx < currentStage;
                const isCurrent = idx === currentStage;
                return (
                  <div 
                    key={stage} 
                    className={`flex items-center gap-2.5 transition-opacity duration-300 ${
                      isCompleted ? "opacity-100 font-medium" : isCurrent ? "opacity-100 font-semibold text-violet-400" : "opacity-40"
                    }`}
                  >
                    <div className={`h-4 w-4 rounded-full flex items-center justify-center border text-[9px] shrink-0 ${
                      isCompleted ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500" : isCurrent ? "bg-violet-500/10 border-violet-500/30 text-violet-500" : "border-muted-foreground/30 text-muted-foreground"
                    }`}>
                      {isCompleted ? "✓" : idx + 1}
                    </div>
                    <span className="text-xs">{stage}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Resume Review dashboard page (Parsed data form) */}
        {parsedData && (
          <div className="space-y-6">
            {/* Header info profile card */}
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1.5 w-full">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-[10px] uppercase font-bold text-violet-400 tracking-widest bg-violet-500/10 px-2 py-0.5 rounded-full border border-violet-500/20">
                      AI Review Required
                    </span>
                    {parsedData.resume_id && parsedData.resume_id !== 'new' && (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase">Resume Label:</span>
                        <Input
                          value={resumeTitle}
                          onChange={(e) => setResumeTitle(e.target.value)}
                          onBlur={handleRenameResume}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              (e.target as HTMLInputElement).blur();
                            }
                          }}
                          className="h-6 text-[10px] bg-background/50 border border-border px-2 w-48 rounded"
                          placeholder="Name this resume..."
                        />
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button 
                      onClick={() => {
                        setParsedData(null);
                        setFileName(null);
                        setResumeTitle("");
                      }}
                      size="sm" 
                      variant="outline" 
                      className="text-xs h-7 px-3 rounded-full"
                    >
                      Upload New Resume
                    </Button>
                    {parsedData.resume_id && parsedData.resume_id !== 'new' && (
                      <Button
                        onClick={handleDeleteResume}
                        size="sm"
                        variant="ghost"
                        className="text-xs h-7 px-3 rounded-full text-destructive hover:text-destructive hover:bg-destructive/10 border border-transparent hover:border-destructive/20 transition-all flex items-center"
                      >
                        <Trash2 className="h-3.5 w-3.5 mr-1" />
                        Delete Profile
                      </Button>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Input 
                    value={parsedData.full_name || ""} 
                    onChange={(e) => handleMetaChange("full_name", e.target.value)}
                    className="text-xl font-bold tracking-tight bg-transparent border-none p-0 focus-visible:ring-0 w-full h-8"
                    placeholder="Candidate Name"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Summary Statement</label>
                  <textarea 
                    value={parsedData.summary} 
                    onChange={(e) => handleMetaChange("summary", e.target.value)}
                    rows={2}
                    className="w-full text-xs bg-transparent border border-border rounded-md px-3 py-2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                </div>
              </div>
              <div className="bg-muted/10 border border-border p-4 rounded-xl text-center shrink-0 flex flex-col justify-center min-w-[140px] w-full md:w-auto">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block">Parser Confidence</span>
                <span className="text-2xl font-black text-emerald-500 my-0.5">
                  {parsedData.confidence_score ? `${Math.round(parsedData.confidence_score * 100)}%` : "N/A"}
                </span>
                <span className="text-[9px] text-muted-foreground">via {parsedData.parser_provider} ({parsedData.parser_model})</span>
              </div>
            </div>

            {/* Horizontal Tabs Bar */}
            <div className="flex flex-wrap gap-2 border-b border-border pb-2">
              <Button 
                onClick={() => setActiveTab('experience')}
                variant={activeTab === 'experience' ? 'secondary' : 'ghost'} 
                className="text-xs font-semibold px-4 py-2"
              >
                <Briefcase className="h-4 w-4 mr-2" />
                Work Experience ({parsedData.work_experiences.length})
              </Button>
              <Button 
                onClick={() => setActiveTab('education')}
                variant={activeTab === 'education' ? 'secondary' : 'ghost'} 
                className="text-xs font-semibold px-4 py-2"
              >
                <BookOpen className="h-4 w-4 mr-2" />
                Education ({parsedData.education.length})
              </Button>
              <Button 
                onClick={() => setActiveTab('projects')}
                variant={activeTab === 'projects' ? 'secondary' : 'ghost'} 
                className="text-xs font-semibold px-4 py-2"
              >
                <Wrench className="h-4 w-4 mr-2" />
                Projects ({parsedData.projects.length})
              </Button>
              <Button 
                onClick={() => setActiveTab('skills')}
                variant={activeTab === 'skills' ? 'secondary' : 'ghost'} 
                className="text-xs font-semibold px-4 py-2"
              >
                <Award className="h-4 w-4 mr-2" />
                Skills & Honors
              </Button>
            </div>

            {/* Form Content pane */}
            <Card className="bg-card border border-border shadow-sm w-full">
              <CardContent className="p-6 space-y-6">
                  {/* WORK EXPERIENCE EDIT TAB */}
                  {activeTab === 'experience' && (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold flex items-center gap-1.5">
                          <Briefcase className="h-4 w-4 text-muted-foreground" />
                          Work Experience
                        </h4>
                        <Button onClick={addExperience} size="sm" variant="outline" className="text-xs h-7 px-3 rounded-full">
                          <Plus className="h-3 w-3 mr-1" /> Add Job
                        </Button>
                      </div>

                      {parsedData.work_experiences.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-6">No experience records detected.</p>
                      )}

                      {parsedData.work_experiences.map((exp, idx) => (
                        <div key={idx} className="p-4 bg-muted/5 border border-border/60 rounded-xl space-y-4 relative">
                          <Button 
                            onClick={() => removeExperience(idx)}
                            size="icon" 
                            variant="ghost" 
                            className="absolute top-2 right-2 text-muted-foreground hover:text-destructive h-7 w-7"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Company Name</label>
                              <Input 
                                value={exp.company} 
                                onChange={(e) => handleExpChange(idx, 'company', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Role / Title</label>
                              <Input 
                                value={exp.role} 
                                onChange={(e) => handleExpChange(idx, 'role', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Location</label>
                              <Input 
                                value={exp.location || ''} 
                                onChange={(e) => handleExpChange(idx, 'location', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                                placeholder="e.g. San Francisco, CA"
                              />
                            </div>
                            <div className="space-y-1 flex items-end">
                              <label className="flex items-center gap-2 text-xs font-semibold cursor-pointer mb-2">
                                <input 
                                  type="checkbox"
                                  checked={exp.is_current}
                                  onChange={(e) => handleExpChange(idx, 'is_current', e.target.checked)}
                                  className="rounded border-border text-violet-500 focus:ring-violet-500 h-4 w-4 bg-background/50"
                                />
                                This is my current job
                              </label>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Start Date</label>
                              <Input 
                                type="text"
                                placeholder="YYYY-MM-DD"
                                value={exp.start_date || ''} 
                                onChange={(e) => handleExpChange(idx, 'start_date', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">End Date</label>
                              <Input 
                                type="text"
                                placeholder="YYYY-MM-DD"
                                disabled={exp.is_current}
                                value={exp.is_current ? '' : (exp.end_date || '')} 
                                onChange={(e) => handleExpChange(idx, 'end_date', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-muted-foreground uppercase">Responsibilities & Achievements</label>
                            <textarea 
                              value={exp.description} 
                              onChange={(e) => handleExpChange(idx, 'description', e.target.value)} 
                              rows={3}
                              className="w-full text-xs bg-background/40 border border-input rounded-md px-3 py-2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* EDUCATION EDIT TAB */}
                  {activeTab === 'education' && (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold flex items-center gap-1.5">
                          <BookOpen className="h-4 w-4 text-muted-foreground" />
                          Education
                        </h4>
                        <Button onClick={addEducation} size="sm" variant="outline" className="text-xs h-7 px-3 rounded-full">
                          <Plus className="h-3 w-3 mr-1" /> Add School
                        </Button>
                      </div>

                      {parsedData.education.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-6">No education records detected.</p>
                      )}

                      {parsedData.education.map((edu, idx) => (
                        <div key={idx} className="p-4 bg-muted/5 border border-border/60 rounded-xl space-y-4 relative">
                          <Button 
                            onClick={() => removeEducation(idx)}
                            size="icon" 
                            variant="ghost" 
                            className="absolute top-2 right-2 text-muted-foreground hover:text-destructive h-7 w-7"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Institution / School</label>
                              <Input 
                                value={edu.institution} 
                                onChange={(e) => handleEduChange(idx, 'institution', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Degree</label>
                              <Input 
                                value={edu.degree} 
                                onChange={(e) => handleEduChange(idx, 'degree', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                                placeholder="e.g. BS, MS"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Field of Study</label>
                              <Input 
                                value={edu.field_of_study} 
                                onChange={(e) => handleEduChange(idx, 'field_of_study', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                                placeholder="e.g. Computer Science"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">GPA</label>
                              <Input 
                                type="number"
                                step="0.01"
                                value={edu.gpa || ''} 
                                onChange={(e) => handleEduChange(idx, 'gpa', e.target.value ? parseFloat(e.target.value) : null)} 
                                className="h-8 text-xs bg-background/50"
                                placeholder="e.g. 3.8"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Start Date</label>
                              <Input 
                                type="text"
                                placeholder="YYYY-MM-DD"
                                value={edu.start_date || ''} 
                                onChange={(e) => handleEduChange(idx, 'start_date', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">End Date</label>
                              <Input 
                                type="text"
                                placeholder="YYYY-MM-DD"
                                value={edu.end_date || ''} 
                                onChange={(e) => handleEduChange(idx, 'end_date', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* PROJECTS EDIT TAB */}
                  {activeTab === 'projects' && (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold flex items-center gap-1.5">
                          <Wrench className="h-4 w-4 text-muted-foreground" />
                          Projects
                        </h4>
                        <Button onClick={addProject} size="sm" variant="outline" className="text-xs h-7 px-3 rounded-full">
                          <Plus className="h-3 w-3 mr-1" /> Add Project
                        </Button>
                      </div>

                      {parsedData.projects.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-6">No project records detected.</p>
                      )}

                      {parsedData.projects.map((proj, idx) => (
                        <div key={idx} className="p-4 bg-muted/5 border border-border/60 rounded-xl space-y-4 relative">
                          <Button 
                            onClick={() => removeProject(idx)}
                            size="icon" 
                            variant="ghost" 
                            className="absolute top-2 right-2 text-muted-foreground hover:text-destructive h-7 w-7"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Project Title</label>
                              <Input 
                                value={proj.title} 
                                onChange={(e) => handleProjectChange(idx, 'title', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-[10px] font-bold text-muted-foreground uppercase">Candidate Role</label>
                              <Input 
                                value={proj.role || ''} 
                                onChange={(e) => handleProjectChange(idx, 'role', e.target.value)} 
                                className="h-8 text-xs bg-background/50"
                                placeholder="e.g. Lead Architect, Core Dev"
                              />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-muted-foreground uppercase">Project URL / Link</label>
                            <Input 
                              value={proj.url || ''} 
                              onChange={(e) => handleProjectChange(idx, 'url', e.target.value)} 
                              className="h-8 text-xs bg-background/50"
                              placeholder="e.g. https://github.com/..."
                            />
                          </div>

                          <div className="space-y-1">
                            <label className="text-[10px] font-bold text-muted-foreground uppercase">Project Description</label>
                            <textarea 
                              value={proj.description} 
                              onChange={(e) => handleProjectChange(idx, 'description', e.target.value)} 
                              rows={2}
                              className="w-full text-xs bg-background/40 border border-input rounded-md px-3 py-2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* SKILLS & ADDITIONAL INFO EDIT TAB */}
                  {activeTab === 'skills' && (
                    <div className="space-y-6">
                      {/* Skills Grid */}
                      <div className="space-y-3">
                        <label className="text-xs font-bold text-muted-foreground uppercase block">Skills List</label>
                        <div className="flex flex-wrap gap-2 p-3 bg-muted/5 border border-border/60 rounded-xl min-h-[50px]">
                          {parsedData.skills.map((skill, idx) => (
                            <span 
                              key={idx} 
                              className="inline-flex items-center gap-1 bg-violet-500/10 text-violet-400 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-violet-500/20"
                            >
                              {skill.name}
                              <button onClick={() => removeSkill(idx)} className="hover:text-destructive text-[10px] font-bold ml-1">×</button>
                            </span>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <Input id="new-skill-input" placeholder="Add a technology..." className="h-8 text-xs max-w-[200px]" />
                          <Button 
                            onClick={() => {
                              const input = document.getElementById('new-skill-input') as HTMLInputElement;
                              if (input) {
                                addSkill(input.value);
                                input.value = '';
                              }
                            }} 
                            size="sm" 
                            variant="outline" 
                            className="h-8 text-xs font-semibold"
                          >
                            Add
                          </Button>
                        </div>
                      </div>

                      {/* Certifications Block */}
                      <div className="space-y-3">
                        <label className="text-xs font-bold text-muted-foreground uppercase block">Certifications</label>
                        <div className="flex flex-wrap gap-2 p-3 bg-muted/5 border border-border/60 rounded-xl min-h-[50px]">
                          {parsedData.certifications.map((cert, idx) => (
                            <span 
                              key={idx} 
                              className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-500/20"
                            >
                              {cert}
                              <button onClick={() => removeCert(idx)} className="hover:text-destructive text-[10px] font-bold ml-1">×</button>
                            </span>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <Input id="new-cert-input" placeholder="e.g. AWS Solutions Architect..." className="h-8 text-xs max-w-[250px]" />
                          <Button 
                            onClick={() => {
                              const input = document.getElementById('new-cert-input') as HTMLInputElement;
                              if (input) {
                                addCert(input.value);
                                input.value = '';
                              }
                            }} 
                            size="sm" 
                            variant="outline" 
                            className="h-8 text-xs font-semibold"
                          >
                            Add
                          </Button>
                        </div>
                      </div>

                      {/* Achievements Block */}
                      <div className="space-y-3">
                        <label className="text-xs font-bold text-muted-foreground uppercase block">Achievements</label>
                        <div className="space-y-2 p-3 bg-muted/5 border border-border/60 rounded-xl min-h-[50px]">
                          {parsedData.achievements.map((ach, idx) => (
                            <div key={idx} className="flex justify-between items-center gap-2 text-xs p-2 bg-background/50 border border-border/50 rounded-lg">
                              <span>{ach}</span>
                              <Button 
                                onClick={() => removeAchievement(idx)} 
                                variant="ghost" 
                                className="h-5 w-5 p-0 text-muted-foreground hover:text-destructive shrink-0"
                              >
                                ×
                              </Button>
                            </div>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <Input id="new-ach-input" placeholder="e.g. 1st Place out of 500 in Hackathon..." className="h-8 text-xs w-full" />
                          <Button 
                            onClick={() => {
                              const input = document.getElementById('new-ach-input') as HTMLInputElement;
                              if (input) {
                                addAchievement(input.value);
                                input.value = '';
                              }
                            }} 
                            size="sm" 
                            variant="outline" 
                            className="h-8 text-xs font-semibold shrink-0"
                          >
                            Add
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

            {/* Bottom Actions Confirmation Card */}
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-full shrink-0">
                  <Info className="h-5 w-5" />
                </div>
                <div className="space-y-0.5">
                  <h4 className="text-xs font-bold text-foreground">Next Steps: Confirmation Pipeline</h4>
                  <p className="text-[10px] text-muted-foreground max-w-md">
                    Confirmation will persist your parsed resume sections directly into target normalized SQL tables.
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col items-stretch sm:items-end gap-1.5 w-full sm:w-auto">
                <div className="flex items-center gap-2 w-full sm:w-auto">
                  {draftSavedMessage && (
                    <span className="text-[11px] text-emerald-500 font-medium animate-pulse mr-2">
                      {draftSavedMessage}
                    </span>
                  )}
                  <Button
                    onClick={handleSaveDraft}
                    disabled={isSavingDraft}
                    size="default"
                    variant="outline"
                    className="text-xs font-bold px-4"
                  >
                    {isSavingDraft ? "Saving..." : "Save Draft"}
                  </Button>
                  <Button 
                    onClick={() => setShowConfirmModal(true)}
                    size="default" 
                    className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold"
                  >
                    Confirm Resume
                  </Button>
                </div>
                {confirmError && (
                  <span className="text-[10px] text-destructive font-semibold max-w-xs text-center sm:text-right mt-1 animate-pulse">
                    {confirmError}
                  </span>
                )}
              </div>
            </div>
            
            {/* Warning Confirmation Modal Overlay */}
            {showConfirmModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fade-in select-none">
                <Card className="max-w-md w-full border border-border shadow-2xl bg-card">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-full shrink-0">
                        <AlertCircle className="h-5 w-5" />
                      </div>
                      <CardTitle className="text-base font-extrabold text-foreground">Confirm Resume Profile?</CardTitle>
                    </div>
                    <CardDescription className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                      This resume will become your official interview profile and will be used during future interviews.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-0">
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Confirming will persist your education, work history, projects, and skills to SQL relations and run Gemini AI to build your permanent Candidate Profile.
                    </p>
                    <div className="flex justify-end gap-2 pt-2">
                      <Button 
                        onClick={() => setShowConfirmModal(false)}
                        variant="outline" 
                        className="text-xs font-semibold px-4 h-9"
                      >
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleConfirmResume}
                        className="text-xs font-bold px-4 h-9 bg-primary hover:bg-primary/90 text-primary-foreground"
                      >
                        Confirm Profile
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export { ResumeIntelligence };
