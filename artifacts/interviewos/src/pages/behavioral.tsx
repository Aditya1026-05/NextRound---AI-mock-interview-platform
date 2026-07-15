import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useInterviewStore } from '@/store/useInterviewStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MessagesSquare, Play, Sparkles, AlertCircle } from 'lucide-react';
import { ScoreBadge } from '@/components/shared/ScoreBadge';

const BEHAVIORAL_TOPICS = [
  { id: '1', title: 'Describe a Complex Challenge', category: 'Conflict & Resolution', score: 88, desc: 'Evaluates your capability to navigate architectural debates and team alignment.' },
  { id: '2', title: 'Handling Tight Deadlines', category: 'Time Management', score: null, desc: 'Focuses on scope pruning, prioritization, and communicating delays.' },
  { id: '3', title: 'Failing to Meet a Goal', category: 'Accountability', score: 79, desc: 'Measures ownership, root cause analysis, and post-mortem execution.' },
  { id: '4', title: 'Disagreeing with a Decision', category: 'Disagreement & Commit', score: 85, desc: 'Tests how you challenge ideas constructively and execute aligned paths.' },
] as const;

export default function Behavioral() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const { startSession } = useInterviewStore();

  useEffect(() => {
    setBreadcrumbs(['Practice Hub', 'Behavioral Preparation']);
  }, [setBreadcrumbs]);

  const handleStartSession = (title: string) => {
    startSession({
      id: Math.random().toString(36).substr(2, 9),
      role: 'Staff Engineer',
      company: 'General Practice',
      type: 'behavioral',
    });
    setLocation('/interviews/session/active');
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 select-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold tracking-tight">Behavioral Mocking</h2>
            <p className="text-muted-foreground text-sm">
              STAR method evaluation, leadership indicators, communications breakdowns, and post-response grading.
            </p>
          </div>
        </div>

        {/* Tips info box */}
        <div className="p-4 bg-violet-500/5 border border-violet-500/10 rounded-xl text-xs flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-violet-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-violet-700 dark:text-violet-300">STAR Methodology Integration</p>
            <p className="text-muted-foreground leading-relaxed">
              When answering behavioral questions, structure your thoughts into **Situation**, **Task**, **Action**, and **Result**. The AI evaluates these parameters to build response scores.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {BEHAVIORAL_TOPICS.map((topic) => (
            <Card key={topic.id} className="hover:border-foreground/20 transition-colors flex flex-col justify-between">
              <CardHeader className="p-6 pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground tracking-wider uppercase">
                      {topic.category}
                    </span>
                    <h3 className="font-bold text-sm text-foreground mt-1 select-text">{topic.title}</h3>
                  </div>
                  {topic.score && (
                    <ScoreBadge score={topic.score} size="sm" className="shrink-0" />
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-6 pt-0 pb-4 flex-1">
                <p className="text-xs text-muted-foreground leading-relaxed select-text">{topic.desc}</p>
              </CardContent>
              <CardContent className="p-6 pt-0 pb-4 border-t border-border/40 flex items-center justify-end">
                <Button 
                  size="sm" 
                  onClick={() => handleStartSession(topic.title)}
                  className="rounded-md text-[10px] gap-1 h-8 bg-foreground text-background hover:bg-foreground/90 border-0 font-semibold"
                >
                  <Play className="h-3 w-3 fill-current" />
                  Start Audio Practice
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
export { Behavioral };
