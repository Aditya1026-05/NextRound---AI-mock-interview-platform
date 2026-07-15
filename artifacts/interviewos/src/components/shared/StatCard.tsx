import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface StatCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: string;
  trendType?: 'positive' | 'negative' | 'neutral';
  className?: string;
}

export function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  trendType = 'neutral',
  className,
}: StatCardProps) {
  return (
    <Card className={cn("overflow-hidden select-none hover:shadow-md transition-shadow duration-300", className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
          {Icon && (
            <div className="p-2 rounded-lg bg-secondary text-foreground shrink-0 border border-border">
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-foreground select-text">
            {value}
          </span>
        </div>

        {trend && (
          <div className="mt-2.5 flex items-center gap-1">
            <span
              className={cn(
                "text-xs font-semibold px-2 py-0.5 rounded-full shrink-0",
                trendType === 'positive' && "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
                trendType === 'negative' && "bg-rose-500/10 text-rose-700 dark:text-rose-400",
                trendType === 'neutral' && "bg-muted text-muted-foreground"
              )}
            >
              {trend}
            </span>
            <span className="text-[10px] text-muted-foreground">vs last cycle</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
export default StatCard;
