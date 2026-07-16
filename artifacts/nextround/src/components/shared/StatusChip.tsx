import React from 'react';
import { cn } from '@/lib/utils';

export type StatusType = 'idle' | 'recording' | 'coding' | 'submitting' | 'completed' | 'upcoming' | 'analyzing' | 'failed';

export interface StatusChipProps {
  status: StatusType;
  className?: string;
}

export function StatusChip({ status, className }: StatusChipProps) {
  const getStyles = () => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20';
      case 'recording':
      case 'coding':
        return 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/20 animate-pulse';
      case 'submitting':
      case 'analyzing':
        return 'bg-violet-500/10 text-violet-700 dark:text-violet-400 border-violet-500/20 animate-pulse';
      case 'upcoming':
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20';
      case 'failed':
        return 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20';
      case 'idle':
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const getLabel = () => {
    switch (status) {
      case 'recording':
        return 'AI Listening';
      case 'submitting':
        return 'Submitting';
      case 'analyzing':
        return 'AI Analyzing';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase border select-none",
      getStyles(),
      className
    )}>
      {/* Ping indicator for live states */}
      {(status === 'recording' || status === 'coding' || status === 'analyzing') && (
        <span className="relative flex h-1.5 w-1.5 shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-current"></span>
        </span>
      )}
      <span>{getLabel()}</span>
    </span>
  );
}
export default StatusChip;
