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

  const getCompanyColorClass = () => {
    // Return Google color-matching backgrounds for visual interest
    switch (company.toLowerCase()) {
      case 'stripe': return 'bg-[#4285F4]/10 text-[#4285F4]';
      case 'vercel': return 'bg-black text-white dark:bg-white dark:text-black';
      case 'google': return 'bg-[#34A853]/10 text-[#34A853]';
      case 'meta': return 'bg-[#4285F4]/10 text-[#4285F4]';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card 
      onClick={onClick}
      className={cn(
        "overflow-hidden hover:border-foreground/15 hover:shadow-md transition-all duration-300 select-none rounded-2xl bg-card/60 backdrop-blur-md border border-border/50",
        onClick && "cursor-pointer active:scale-[0.99]",
        className
      )}
    >
      <CardHeader className="p-5 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5 min-w-0">
            <h3 className="font-extrabold text-base leading-tight text-foreground truncate select-text">
              {role}
            </h3>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0",
                getCompanyColorClass()
              )}>
                {company.charAt(0)}
              </span>
              <span className="truncate font-medium select-text">{company}</span>
            </div>
          </div>
          <ScoreBadge score={score} size="sm" className="shrink-0 rounded-full" />
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-0 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <StatusChip status={status} className="rounded-full" />
          <span className="inline-flex items-center gap-1 text-[10px] font-bold tracking-wider text-muted-foreground uppercase bg-muted/65 border border-border/40 px-3 py-1 rounded-full select-none">
            <FileText className="h-3 w-3 shrink-0" />
            {getTypeText()}
          </span>
        </div>
      </CardContent>

      <CardFooter className="p-5 pt-0 border-t border-border/30 flex items-center justify-between text-[10px] font-medium text-muted-foreground">
        <div className="flex items-center gap-1.5 select-text">
          <Calendar className="h-3.5 w-3.5 shrink-0 text-muted-foreground/80" />
          <span>{date}</span>
        </div>

        {tags.length > 0 && (
          <div className="flex items-center gap-1 max-w-[50%] truncate select-none">
            <Tag className="h-3 w-3 shrink-0 text-muted-foreground/80" />
            <span className="truncate">{tags.join(', ')}</span>
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
export default InterviewCard;
