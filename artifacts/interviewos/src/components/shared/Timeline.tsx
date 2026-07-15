import React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

export interface TimelineItem {
  id: string;
  title: string;
  description?: string;
  date?: string;
  status: 'completed' | 'current' | 'upcoming';
}

export interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

export function Timeline({ items, className }: TimelineProps) {
  return (
    <div className={cn("flow-root select-none", className)}>
      <ul className="-mb-8">
        {items.map((item, itemIdx) => (
          <li key={item.id}>
            <div className="relative pb-8">
              {itemIdx !== items.length - 1 ? (
                <span
                  className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-border"
                  aria-hidden="true"
                />
              ) : null}
              <div className="relative flex space-x-3 items-start">
                <div>
                  <span
                    className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-background border shrink-0",
                      item.status === 'completed' && "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400",
                      item.status === 'current' && "bg-indigo-500/10 border-indigo-500/30 text-indigo-600 dark:text-indigo-400 animate-pulse",
                      item.status === 'upcoming' && "bg-muted border-border text-muted-foreground"
                    )}
                  >
                    {item.status === 'completed' && <CheckCircle2 className="h-4 w-4" />}
                    {item.status === 'current' && <Clock className="h-4 w-4" />}
                    {item.status === 'upcoming' && <Circle className="h-3 w-3" />}
                  </span>
                </div>
                <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground select-text">
                      {item.title}
                    </p>
                    {item.description && (
                      <p className="text-xs text-muted-foreground select-text">
                        {item.description}
                      </p>
                    )}
                  </div>
                  {item.date && (
                    <div className="whitespace-nowrap text-right text-xs text-muted-foreground pt-0.5 font-medium select-text">
                      <time dateTime={item.date}>{item.date}</time>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
export default Timeline;
