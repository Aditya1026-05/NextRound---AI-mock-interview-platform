import React, { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useInterviewStore } from '@/store/useInterviewStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Code2, MessagesSquare, Laptop, Cpu, PlusCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const INTERVIEW_TYPES = [
  { id: 'coding', title: 'Coding Interview', desc: 'Algorithms, data structures, and code execution.', icon: Code2 },
  { id: 'behavioral', title: 'Behavioral prep', desc: 'STAR methodology, leadership, conflict resolution.', icon: MessagesSquare },
  { id: 'system-design', title: 'System Design', desc: 'Scalability, microservices, system architecture.', icon: Laptop },
  { id: 'ml', title: 'Machine Learning', desc: 'Deep learning, model training, ML design.', icon: Cpu },
] as const;

export default function InterviewNew() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const { startSession } = useInterviewStore();

  const [role, setRole] = useState('Senior Software Engineer');
  const [company, setCompany] = useState('Stripe');
  const [selectedType, setSelectedType] = useState<'coding' | 'behavioral' | 'system-design' | 'ml'>('coding');

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'New Interview']);
  }, [setBreadcrumbs]);

  const handleStart = () => {
    startSession({
      id: Math.random().toString(36).substr(2, 9),
      role,
      company,
      type: selectedType,
    });
    setLocation('/interviews/session/active');
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6 select-none">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Configure Interview</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Specify target roles, companies, and category for AI personalization.
          </p>
        </div>

        <Card className="border border-border">
          <CardHeader className="p-6">
            <CardTitle className="text-lg">Interview Details</CardTitle>
            <CardDescription className="text-xs">Provide details to align the AI interviewer parameters.</CardDescription>
          </CardHeader>
          <CardContent className="p-6 pt-0 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="role" className="text-xs font-semibold">Target Position</Label>
                <Input 
                  id="role" 
                  value={role} 
                  onChange={(e) => setRole(e.target.value)} 
                  placeholder="e.g. Senior Frontend Engineer"
                  className="h-9 text-xs"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company" className="text-xs font-semibold">Target Company</Label>
                <Input 
                  id="company" 
                  value={company} 
                  onChange={(e) => setCompany(e.target.value)} 
                  placeholder="e.g. Stripe"
                  className="h-9 text-xs"
                />
              </div>
            </div>

            <div className="space-y-2.5">
              <Label className="text-xs font-semibold">Interview Category</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {INTERVIEW_TYPES.map((type) => {
                  const Icon = type.icon;
                  const isSelected = selectedType === type.id;
                  return (
                    <div
                      key={type.id}
                      onClick={() => setSelectedType(type.id)}
                      className={cn(
                        "p-4 rounded-xl border border-border bg-card hover:border-foreground/20 cursor-pointer transition-all duration-200 select-none flex flex-col justify-between h-32",
                        isSelected && "border-foreground ring-1 ring-foreground"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="p-2 rounded-lg bg-secondary text-foreground shrink-0 border border-border">
                          <Icon className="h-4 w-4" />
                        </div>
                        {isSelected && (
                          <span className="w-2 h-2 rounded-full bg-foreground" />
                        )}
                      </div>
                      <div className="space-y-1">
                        <h4 className="font-bold text-xs text-foreground leading-none">{type.title}</h4>
                        <p className="text-[10px] text-muted-foreground leading-tight">{type.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
          <CardFooter className="p-6 border-t border-border flex items-center justify-end">
            <Button
              onClick={handleStart}
              className="rounded-md gap-1.5 text-xs bg-foreground text-background hover:bg-foreground/90 h-9"
            >
              <PlusCircle className="h-4 w-4" />
              Generate Session & Start
            </Button>
          </CardFooter>
        </Card>
      </div>
    </DashboardLayout>
  );
}
