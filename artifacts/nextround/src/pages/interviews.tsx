import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Code2, MessagesSquare, Laptop, Cpu, Plus } from 'lucide-react';

const PREP_CATEGORIES = [
  { id: 'coding', title: 'Coding Workspace', desc: 'Solve algorithm questions using our live sandbox editor and test runner.', icon: Code2, href: '/coding' },
  { id: 'behavioral', title: 'Behavioral Mocking', desc: 'Practice situational queries using voice analysis & STAR structures.', icon: MessagesSquare, href: '/behavioral' },
  { id: 'system-design', title: 'System Design Architecture', desc: 'Design scalable, high-availability caching architectures.', icon: Laptop, href: '/system-design' },
  { id: 'ml', title: 'Machine Learning Pipelines', desc: 'Build real-time feature models, recommendation systems, and pipelines.', icon: Cpu, href: '/ml' },
] as const;

export default function Interviews() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Interview Modules']);
  }, [setBreadcrumbs]);

  return (
    <DashboardLayout>
      <div className="space-y-6 select-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight">Practice Modules</h2>
            <p className="text-muted-foreground text-sm mt-1">
              Select an interview category to configure mock sessions with our adaptive AI interviewers.
            </p>
          </div>
          <Button 
            onClick={() => setLocation('/interviews/new')}
            className="rounded-md text-xs gap-1.5 h-9 bg-foreground text-background hover:bg-foreground/90 border-0"
          >
            <Plus className="h-4 w-4" />
            Launch AI session
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {PREP_CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            return (
              <Card 
                key={cat.id} 
                onClick={() => setLocation(cat.href)}
                className="hover:border-foreground/20 hover:shadow-sm cursor-pointer transition-all duration-300 flex flex-col justify-between"
              >
                <CardHeader className="p-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-secondary text-foreground shrink-0 border border-border">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-base font-bold">{cat.title}</CardTitle>
                  </div>
                  <CardDescription className="text-xs mt-3 leading-relaxed select-text">
                    {cat.desc}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6 pt-0 flex justify-end">
                  <span className="text-xs font-semibold text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
                    Open Hub →
                  </span>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
export { Interviews };
