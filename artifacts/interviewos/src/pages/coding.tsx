import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useInterviewStore } from '@/store/useInterviewStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Code2, Play, Flame, Star, CheckCircle } from 'lucide-react';
import { ScoreBadge } from '@/components/shared/ScoreBadge';

const CODING_QUESTIONS = [
  { id: '1', title: 'Design a Rate Limiter', diff: 'hard', status: 'completed', score: 88, desc: 'Implement sliding-window counters in Redis.' },
  { id: '2', title: 'Merge K Sorted Lists', diff: 'hard', status: 'completed', score: 92, desc: 'Sort linked lists with min-heaps.' },
  { id: '3', title: 'Binary Tree Maximum Path Sum', diff: 'hard', status: 'completed', score: 75, desc: 'Calculate sub-path nodes dfs recursively.' },
  { id: '4', title: 'LRU Cache Design', diff: 'medium', status: 'completed', score: 84, desc: 'Implement hash map with doubly linked lists.' },
  { id: '5', title: 'Longest Palindromic Substring', diff: 'medium', status: 'open', score: null, desc: 'Find palindromes via central expansion.' },
  { id: '6', title: 'Two Sum Map Resolution', diff: 'easy', status: 'open', score: null, desc: 'Resolve pair matches in O(N) complexity.' },
] as const;

export default function Coding() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const { startSession } = useInterviewStore();

  useEffect(() => {
    setBreadcrumbs(['Practice Hub', 'Coding Interviews']);
  }, [setBreadcrumbs]);

  const handleStartQuestion = (qTitle: string) => {
    startSession({
      id: Math.random().toString(36).substr(2, 9),
      role: 'Software Engineer',
      company: 'Self Practice',
      type: 'coding',
    });
    setLocation('/interviews/session/active');
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 select-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold tracking-tight">Coding Workspace</h2>
            <p className="text-muted-foreground text-sm">
              Algorithms, core data structures, performance evaluations, and hidden test suites.
            </p>
          </div>
          <div className="flex gap-2">
            <div className="bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 px-3 py-1 rounded-md text-xs font-mono font-semibold flex items-center gap-1.5">
              <Flame className="h-4 w-4 animate-bounce" />
              <span>3 Day Hot Streak</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CODING_QUESTIONS.map((question) => (
            <Card key={question.id} className="flex flex-col justify-between hover:border-foreground/20 transition-colors">
              <CardHeader className="p-5 pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      question.diff === 'hard' ? 'bg-rose-500/10 text-rose-700 border-rose-500/20' :
                      question.diff === 'medium' ? 'bg-amber-500/10 text-amber-700 border-amber-500/20' :
                      'bg-emerald-500/10 text-emerald-700 border-emerald-500/20'
                    }`}>
                      {question.diff.toUpperCase()}
                    </span>
                    <h3 className="font-bold text-sm text-foreground leading-tight mt-2 select-text">{question.title}</h3>
                  </div>
                  {question.score && (
                    <ScoreBadge score={question.score} size="sm" className="shrink-0" />
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0 pb-4 flex-1">
                <p className="text-xs text-muted-foreground leading-relaxed select-text">{question.desc}</p>
              </CardContent>
              <CardContent className="p-5 pt-0 pb-4 border-t border-border/40 flex items-center justify-between">
                <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-semibold">
                  {question.status === 'completed' ? (
                    <>
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                      <span className="text-emerald-600 dark:text-emerald-400">SOLVED</span>
                    </>
                  ) : (
                    <>
                      <Star className="h-3.5 w-3.5" />
                      <span>UNSOLVED</span>
                    </>
                  )}
                </div>
                <Button 
                  size="sm" 
                  onClick={() => handleStartQuestion(question.title)}
                  className="rounded-md text-[10px] gap-1 h-7 bg-foreground text-background hover:bg-foreground/90 border-0 font-semibold"
                >
                  <Play className="h-2.5 w-2.5 fill-current" />
                  Start AI Practice
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
export { Coding };
