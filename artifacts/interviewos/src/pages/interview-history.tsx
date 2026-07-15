import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { InterviewCard } from '@/components/shared/InterviewCard';
import { Button } from '@/components/ui/button';
import { Plus, History } from 'lucide-react';

const PAST_INTERVIEWS = [
  { id: '1', role: 'Frontend Engineer', company: 'Stripe', date: 'Jul 14, 2026', score: 88, status: 'completed', tags: ['React', 'CSS v4'] },
  { id: '2', role: 'Full Stack Engineer', company: 'Vercel', date: 'Jul 12, 2026', score: 92, status: 'completed', tags: ['Next.js', 'Postgres'] },
  { id: '3', role: 'System Design', company: 'Google', date: 'Jul 10, 2026', score: 75, status: 'completed', tags: ['Caching', 'CDN'] },
  { id: '4', role: 'Engineering Manager', company: 'Linear', date: 'Jun 28, 2026', score: 84, status: 'completed', tags: ['Product Strategy', 'Mentoring'] },
  { id: '5', role: 'Backend Engineer', company: 'GitHub', date: 'Jun 22, 2026', score: 78, status: 'completed', tags: ['Go', 'Kafka'] },
  { id: '6', role: 'Software Engineer', company: 'OpenAI', date: 'May 18, 2026', score: 62, status: 'completed', tags: ['PyTorch', 'Transformers'] },
] as const;

export default function InterviewHistory() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Session History']);
  }, [setBreadcrumbs]);

  return (
    <DashboardLayout>
      <div className="space-y-6 select-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight">Session History</h2>
            <p className="text-muted-foreground text-sm mt-1">
              Browse your historical mock interview archives and generated reports.
            </p>
          </div>
          <Button 
            onClick={() => setLocation('/interviews/new')}
            className="rounded-md text-xs gap-1.5 h-9 bg-foreground text-background hover:bg-foreground/90 border-0"
          >
            <Plus className="h-4 w-4" />
            New Interview
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PAST_INTERVIEWS.map((session) => (
            <InterviewCard
              key={session.id}
              id={session.id}
              role={session.role}
              company={session.company}
              type={session.id === '3' ? 'system-design' : 'coding'}
              date={session.date}
              score={session.score}
              status={session.status}
              tags={session.tags as any}
              onClick={() => setLocation(`/interviews/session/${session.id}`)}
            />
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
export { InterviewHistory };
