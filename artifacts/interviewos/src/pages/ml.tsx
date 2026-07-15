import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUIStore } from '@/store/useUIStore';
import { useInterviewStore } from '@/store/useInterviewStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Cpu, Play, BrainCircuit } from 'lucide-react';
import { ScoreBadge } from '@/components/shared/ScoreBadge';

const ML_TOPICS = [
  { id: '1', title: 'Design a Recommendation System', score: 88, desc: 'Discuss collaborative filtering, deep learning embed layers, vector search database indexing, and realtime feature stores.' },
  { id: '2', title: 'Design a Large Language Model Pipeline', score: null, desc: 'Discuss fine-tuning datasets, parameter-efficient adapters (LoRA), retrieval-augmented generation (RAG), and tokens pricing.' },
  { id: '3', title: 'Real-time Object Detection Pipeline', score: 68, desc: 'Discuss CNN architectures (YOLO), hardware bottlenecks, precision-recall tradeoffs, and edge device deployments.' },
] as const;

export default function MachineLearning() {
  const [, setLocation] = useLocation();
  const { setBreadcrumbs } = useUIStore();
  const { startSession } = useInterviewStore();

  useEffect(() => {
    setBreadcrumbs(['Practice Hub', 'Machine Learning']);
  }, [setBreadcrumbs]);

  const handleStartSession = (title: string) => {
    startSession({
      id: Math.random().toString(36).substr(2, 9),
      role: 'ML Scientist',
      company: 'General Practice',
      type: 'ml',
    });
    setLocation('/interviews/session/active');
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 select-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold tracking-tight">Machine Learning</h2>
            <p className="text-muted-foreground text-sm">
              Embedding spaces, neural pipeline architectures, fine-tuning adapters, inference latency, and vector indices.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {ML_TOPICS.map((topic) => (
            <Card key={topic.id} className="hover:border-foreground/20 transition-colors flex flex-col justify-between">
              <CardHeader className="p-6 pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground tracking-wider uppercase flex items-center gap-1">
                      <BrainCircuit className="h-3 w-3" />
                      Neural Networks & Pipelines
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
                  Start ML Practice
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
export { MachineLearning };
