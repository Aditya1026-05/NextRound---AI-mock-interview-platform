import React from 'react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { ScoreBadge } from './ScoreBadge';
import { StatusChip, StatusType } from './StatusChip';
import { Calendar, Briefcase, Tag, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface InterviewCardProps {
  id: string;
  role: string;
  company: string;
  type: 'coding' | 'behavioral' | 'system-design' | 'ml';
  date: string;
  score: number | null;
  status: StatusType;
  tags?: string[];
  onClick?: () => void;
  className?: string;
}

export function InterviewCard({
  role,
  company,
  type,
  date,
  score,
  status,
  tags = [],
  onClick,
  className,
}: InterviewCardProps) {
  const getTypeText = () => {
    switch (type) {
      case 'system-design': return 'System Design';
      case 'ml': return 'Machine Learning';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  return (
    <Card 
      onClick={onClick}
      className={cn(
        "overflow-hidden hover:border-foreground/20 hover:shadow-sm transition-all duration-300 select-none",
        onClick && "cursor-pointer active:scale-[0.99]",
        className
      )}
    >
      <CardHeader className="p-5 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1 min-w-0">
            <h3 className="font-bold text-base leading-tight text-foreground truncate select-text">
              {role}
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Briefcase className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate select-text">{company}</span>
            </div>
          </div>
          <ScoreBadge score={score} size="sm" className="shrink-0" />
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-0 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip status={status} />
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold tracking-wider text-muted-foreground uppercase bg-muted border border-border px-2 py-0.5 rounded-full select-none">
            <FileText className="h-3 w-3 shrink-0" />
            {getTypeText()}
          </span>
        </div>
      </CardContent>

      <CardFooter className="p-5 pt-0 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
        <div className="flex items-center gap-1.5 select-text">
          <Calendar className="h-3.5 w-3.5 shrink-0" />
          <span>{date}</span>
        </div>

        {tags.length > 0 && (
          <div className="flex items-center gap-1 max-w-[50%] truncate select-none">
            <Tag className="h-3 w-3 shrink-0" />
            <span className="truncate">{tags.join(', ')}</span>
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
export default InterviewCard;
