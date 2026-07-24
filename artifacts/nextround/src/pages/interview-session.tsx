import React, { useEffect, useState, useRef } from 'react';
import { useRoute, useLocation } from 'wouter';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Send, Play, Bot, User, ArrowLeft, Loader2, MessageSquare, AlertTriangle, X, Clock } from 'lucide-react';
import { apiFetch, ApiError } from '@/lib/apiFetch';

interface Message {
  id: string;
  role: 'SYSTEM' | 'INTERVIEWER' | 'CANDIDATE';
  content: string;
  sequence_number: number;
  created_at: string;
}

interface SessionDetails {
  id: string;
  category: string;
  role: string | null;
  difficulty: string;
  duration_minutes: number;
  status: 'CREATED' | 'READY' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  resume_filename: string;
  blueprint_title: string | null;
  started_at: string | null;
}

export default function InterviewSession() {
  const [, setLocation] = useLocation();
  const [, params] = useRoute('/interviews/session/:id');
  const sessionId = params?.id;

  const isUserStoreLoading = useUserStore((state) => state.isLoading);
  const token = useUserStore((state) => state.token);

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  // Inline non-blocking error banner for send failures
  const [sendError, setSendError] = useState<string | null>(null);
  const [inputVal, setInputVal] = useState('');
  const [sending, setSending] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number>(0);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize and update the countdown timer
  useEffect(() => {
    if (!session) return;
    
    const calculateTimeLeft = () => {
      if (session.status === 'IN_PROGRESS' && session.started_at) {
        const start = new Date(session.started_at).getTime();
        const now = Date.now();
        const elapsed = Math.floor((now - start) / 1000);
        const limit = session.duration_minutes * 60;
        return Math.max(0, limit - elapsed);
      }
      return session.duration_minutes * 60;
    };

    setTimeLeft(calculateTimeLeft());

    let interval: NodeJS.Timeout | undefined;
    if (session.status === 'IN_PROGRESS') {
      interval = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            if (interval) clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [session?.status, session?.started_at, session?.duration_minutes]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Load session configuration details
  const loadSession = async () => {
    if (!sessionId) return;
    try {
      const res = await apiFetch(`/interview/session/${sessionId}`);
      const data = await res.json();
      setSession(data);
    } catch (err: any) {
      setErrorMsg(err instanceof ApiError && err.status === 404
        ? 'Interview session not found.'
        : (err.message || 'Failed to retrieve session details.'));
    }
  };

  // Load historical chat turns
  const loadHistory = async () => {
    if (!sessionId) return;
    try {
      const res = await apiFetch(`/interview/session/${sessionId}/messages`);
      const data = await res.json();
      setMessages(data);
    } catch (err) {
      console.error('Failed to load message history', err);
    }
  };

  const initSession = async () => {
    setLoading(true);
    setErrorMsg(null);
    await Promise.all([loadSession(), loadHistory()]);
    setLoading(false);
  };

  useEffect(() => {
    if (isUserStoreLoading) return;
    if (!token) {
      setLocation('/login');
      return;
    }
    initSession();
  }, [sessionId, token, isUserStoreLoading]);

  // Start the interview and receive the greeting turn
  const handleStartInterview = async () => {
    if (!sessionId || sending) return;
    setSending(true);
    setSendError(null);
    try {
      await apiFetch(`/interview/session/${sessionId}/start`, { method: 'POST' });
      await Promise.all([loadHistory(), loadSession()]);
    } catch (err: any) {
      setSendError(err.message || 'Failed to start the interview. Please try again.');
    } finally {
      setSending(false);
    }
  };

  // Respond to the interviewer
  const handleSendMessage = async () => {
    const trimmed = inputVal.trim();
    if (!trimmed || !sessionId || sending) return;
    setInputVal('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '36px';
    }
    setSending(true);
    setSendError(null);

    // Optimistically push the candidate message locally
    const tempId = `temp-${Date.now()}`;
    const optimisticMessage: Message = {
      id: tempId,
      role: 'CANDIDATE',
      content: trimmed,
      sequence_number: messages.length,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMessage]);

    try {
      await apiFetch(`/interview/session/${sessionId}/respond`, {
        method: 'POST',
        body: JSON.stringify({ message: trimmed }),
      });
      // Reload authoritative messages from backend
      await Promise.all([loadHistory(), loadSession()]);
    } catch (err: any) {
      // Rollback optimistic message — user can retype (their text was cleared, so restore it)
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setInputVal(trimmed); // Restore the typed text so they don't lose it
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        const newHeight = Math.min(textareaRef.current.scrollHeight, 160);
        textareaRef.current.style.height = `${newHeight}px`;
      }
      setSendError(err.message || 'Failed to send your response. Please try again.');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-[60vh] flex flex-col items-center justify-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-xs font-semibold text-muted-foreground">Initializing conversation context...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (errorMsg || !session) {
    return (
      <DashboardLayout>
        <div className="max-w-md mx-auto mt-16 text-center space-y-4">
          <Card className="border-red-500/20 bg-red-500/[0.01] p-6 rounded-2xl shadow">
            <h3 className="text-base font-bold text-foreground">Session Error</h3>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{errorMsg || 'Failed to load details'}</p>
            <div className="pt-4">
              <Button onClick={() => setLocation('/interviews')} size="sm" variant="outline" className="rounded-full text-xs gap-1">
                <ArrowLeft className="h-3 w-3" /> Go Back
              </Button>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const formatRole = (role: string | null) => {
    if (!role) return '';
    return role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col space-y-4 select-none">

        {/* Navigation / Metadata Header */}
        <div className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setLocation('/interviews')}
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full border border-border"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h3 className="text-sm font-extrabold text-foreground select-text">
                {session.blueprint_title || 'Mock Interview Session'}
              </h3>
              <p className="text-[10px] text-muted-foreground select-text">
                Category: {session.category.toUpperCase()} {session.role ? `| Role: ${formatRole(session.role)}` : ''} | Mode: Text
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {session.status === 'IN_PROGRESS' && (
              <span className="text-[10px] font-bold font-mono px-2.5 py-0.5 rounded border border-red-500/25 bg-red-500/10 text-red-500 flex items-center gap-1">
                <Clock className="h-3 w-3 animate-pulse text-red-500" />
                {formatTime(timeLeft)}
              </span>
            )}
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${
              session.status === 'COMPLETED'
                ? 'text-zinc-500 bg-zinc-500/10 border-zinc-500/25'
                : 'text-blue-500 bg-blue-500/10 border-blue-500/25'
            }`}>
              {session.status}
            </span>
          </div>
        </div>

        {/* Non-blocking send error banner */}
        {sendError && (
          <div className="flex items-start gap-2 px-3 py-2.5 bg-red-500/8 border border-red-500/20 rounded-xl text-xs text-red-600 dark:text-red-400 select-text shrink-0">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
            <span className="flex-1 leading-relaxed">{sendError}</span>
            <button onClick={() => setSendError(null)} className="shrink-0 text-red-400 hover:text-red-600">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Chat Workspace */}
        <div className="flex-1 bg-card/40 border border-border/60 rounded-3xl overflow-hidden flex flex-col relative">

          {messages.length === 0 && session.status === 'READY' ? (
            /* Welcome / Start screen */
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-6">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                <MessageSquare className="h-6 w-6 animate-pulse" />
              </div>
              <div className="max-w-md space-y-2">
                <h2 className="text-lg font-extrabold text-foreground">Welcome to your Mock Interview</h2>
                <p className="text-xs text-muted-foreground leading-relaxed select-text">
                  You are paired with the AI Interviewer. The discussion is based on your confirmed resume, target role, and personalized blueprint agenda.
                </p>
              </div>
              <Button
                onClick={handleStartInterview}
                disabled={sending}
                className="bg-[#4285F4] hover:bg-[#3b77db] text-white rounded-xl text-xs font-bold px-6 py-5 gap-1.5 shadow-md shrink-0"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5 fill-current" />
                )}
                Start Interview
              </Button>
            </div>
          ) : (
            /* Conversation Panel */
            <div className="flex-1 flex flex-col overflow-hidden">

              {/* Message Transcript */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4 select-text">
                {messages.map((msg) => {
                  const isInterviewer = msg.role === 'INTERVIEWER';
                  return (
                    <div
                      key={msg.id}
                      className={`flex gap-3 max-w-[85%] ${
                        isInterviewer ? 'mr-auto' : 'ml-auto flex-row-reverse'
                      }`}
                    >
                      <div className={`w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 text-[10px] select-none ${
                        isInterviewer
                          ? 'bg-foreground border-transparent text-background font-bold'
                          : 'bg-muted border-border text-foreground font-semibold'
                      }`}>
                        {isInterviewer ? <Bot className="h-3.5 w-3.5" /> : <User className="h-3.5 w-3.5" />}
                      </div>
                      <div className={`p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                        isInterviewer
                          ? 'bg-background text-foreground border border-border/80 rounded-tl-none shadow-sm'
                          : 'bg-foreground text-background border border-transparent rounded-tr-none shadow'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  );
                })}

                {/* Thinking indicator */}
                {sending && (
                  <div className="flex gap-3 max-w-[85%] mr-auto items-center">
                    <div className="w-7 h-7 rounded-lg bg-foreground border border-transparent text-background flex items-center justify-center shrink-0">
                      <Bot className="h-3.5 w-3.5" />
                    </div>
                    <div className="p-3 bg-background border border-border/80 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      <span className="text-[10px] font-semibold text-muted-foreground">Interviewer is thinking...</span>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {/* Input Toolbar */}
              <div className="p-4 border-t border-border/50 shrink-0 bg-card/65 select-none">
                {session.status === 'COMPLETED' ? (
                  <div className="text-center py-2 text-xs font-bold text-zinc-500 bg-zinc-500/10 border border-zinc-500/20 rounded-xl">
                    Interview Completed. You can review the conversation above or exit.
                  </div>
                ) : (
                  <div className="flex items-start rounded-xl border border-border/80 bg-background focus-within:border-foreground/35 px-2 py-1 shadow-sm">
                    <style>{`
                      textarea.scrollbar-none::-webkit-scrollbar {
                        display: none;
                      }
                    `}</style>
                    <Textarea
                      ref={textareaRef}
                      placeholder="Type your response here..."
                      value={inputVal}
                      onChange={(e) => {
                        setInputVal(e.target.value);
                        e.target.style.height = '36px';
                        const newHeight = Math.min(e.target.scrollHeight, 160);
                        e.target.style.height = `${newHeight}px`;
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      disabled={sending}
                      className="border-transparent focus-visible:ring-0 text-xs py-2 min-h-[36px] max-h-[160px] h-[36px] resize-none shadow-none flex-1 bg-transparent placeholder:text-muted-foreground/65 scrollbar-none"
                      style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={sending || !inputVal.trim()}
                      size="icon"
                      className="h-8 w-8 rounded-lg bg-foreground text-background hover:bg-foreground/90 shrink-0 mt-0.5"
                    >
                      <Send className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}
                <div className="flex justify-between items-center mt-2 px-1 text-[9px] text-muted-foreground">
                  <span>Press Enter to submit, Shift + Enter for new line</span>
                  <span>Conversation is logged securely</span>
                </div>
              </div>

            </div>
          )}

        </div>

      </div>
    </DashboardLayout>
  );
}
