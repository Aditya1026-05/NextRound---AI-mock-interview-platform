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
  { id: 'coding', title: 'Coding Interview', desc: 'Algorithms, data structures, and code execution.', icon: Code2, color: '#4285F4' },
  { id: 'behavioral', title: 'Behavioral Prep', desc: 'STAR methodology, leadership, conflict resolution.', icon: MessagesSquare, color: '#34A853' },
  { id: 'system-design', title: 'System Design', desc: 'Scalability, microservices, system architecture.', icon: Laptop, color: '#FBBC05' },
  { id: 'ml', title: 'Machine Learning', desc: 'Deep learning, model training, ML design.', icon: Cpu, color: '#EA4335' },
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
      <div className="max-w-2xl mx-auto space-y-6 select-none relative">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Configure Interview</h2>
          <p className="text-muted-foreground text-sm mt-1 select-text">
            Specify target roles, companies, and category for AI personalization.
          </p>
        </div>

        <Card className="border border-border/50 rounded-2xl bg-card/65 backdrop-blur-md shadow-sm">
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
                  className="h-10 text-xs rounded-full px-4 border-border hover:border-foreground/10 focus:border-foreground/30 focus:ring-0 bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company" className="text-xs font-semibold">Target Company</Label>
                <Input 
                  id="company" 
                  value={company} 
                  onChange={(e) => setCompany(e.target.value)} 
                  placeholder="e.g. Stripe"
                  className="h-10 text-xs rounded-full px-4 border-border hover:border-foreground/10 focus:border-foreground/30 focus:ring-0 bg-background/50"
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
                        "p-5 rounded-2xl border border-border bg-card/50 hover:border-foreground/15 cursor-pointer transition-all duration-200 select-none flex flex-col justify-between h-36 relative overflow-hidden",
                        isSelected && "border-[#4285F4] ring-1 ring-[#4285F4] bg-[#4285F4]/[0.02]"
                      )}
                    >
                      {/* Brand highlighted color dot */}
                      <span className="absolute top-3 right-3 w-2.5 h-2.5 rounded-full" style={{ backgroundColor: type.color }} />
                      
                      <div className="flex items-center justify-between">
                        <div 
                          className="p-3 rounded-full shrink-0 border border-border/30 text-white"
                          style={{ backgroundColor: type.color }}
                        >
                          <Icon className="h-4.5 w-4.5" />
                        </div>
                      </div>
                      <div className="space-y-1 mt-2">
                        <h4 className="font-bold text-sm text-foreground leading-none">{type.title}</h4>
                        <p className="text-[10px] text-muted-foreground leading-snug select-text">{type.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
          <CardFooter className="p-6 border-t border-border/40 flex items-center justify-end">
            <Button
              onClick={handleStart}
              className="rounded-full gap-1.5 text-xs bg-[#4285F4] hover:bg-[#3b77db] text-white border-0 h-10 px-5 shadow-sm transition-colors font-semibold"
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
export { InterviewNew };
