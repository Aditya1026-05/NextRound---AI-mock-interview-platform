import React from 'react';
import { cn } from '@/lib/utils';

export interface ScoreBadgeProps {
  score: number | null;
  maxScore?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreBadge({
  score,
  maxScore = 100,
  className,
  size = 'md',
}: ScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className={cn(
        "inline-flex items-center justify-center font-mono rounded-md bg-muted text-muted-foreground border border-border",
        size === 'sm' && "text-[10px] px-1.5 py-0.5",
        size === 'md' && "text-xs px-2.5 py-1",
        size === 'lg' && "text-sm px-3.5 py-1.5",
        className
      )}>
        --
      </span>
    );
  }

  const percentage = (score / maxScore) * 100;
  
  const isHigh = percentage >= 85;
  const isMed = percentage >= 70 && percentage < 85;
  
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center font-mono font-bold rounded-md border transition-colors",
        isHigh && "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20",
        isMed && "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20",
        !isHigh && !isMed && "bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20",
        size === 'sm' && "text-[10px] px-1.5 py-0.5",
        size === 'md' && "text-xs px-2.5 py-1",
        size === 'lg' && "text-sm px-3.5 py-1.5",
        className
      )}
    >
      {score}/{maxScore}
    </span>
  );
}
export default ScoreBadge;
