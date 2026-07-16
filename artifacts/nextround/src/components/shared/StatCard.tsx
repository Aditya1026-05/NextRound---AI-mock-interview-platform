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
  colorTheme?: 'blue' | 'green' | 'yellow' | 'red' | 'indigo';
  className?: string;
}

export function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  trendType = 'neutral',
  colorTheme = 'blue',
  className,
}: StatCardProps) {
  const getThemeColorClass = () => {
    switch (colorTheme) {
      case 'green': return 'text-[#34A853] bg-[#34A853]/10 border-[#34A853]/20';
      case 'yellow': return 'text-[#FBBC05] bg-[#FBBC05]/10 border-[#FBBC05]/20';
      case 'red': return 'text-[#EA4335] bg-[#EA4335]/10 border-[#EA4335]/20';
      case 'indigo': return 'text-indigo-600 bg-indigo-500/10 border-indigo-500/20';
      case 'blue':
      default:
        return 'text-[#4285F4] bg-[#4285F4]/10 border-[#4285F4]/20';
    }
  };

  return (
    <Card className={cn(
      "overflow-hidden select-none hover:shadow-md hover:border-foreground/15 transition-all duration-300 rounded-2xl bg-card/65 backdrop-blur-md border border-border/50",
      className
    )}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
          {Icon && (
            <div className={cn(
              "p-2.5 rounded-full shrink-0 border",
              getThemeColorClass()
            )}>
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold tracking-tight text-foreground select-text">
            {value}
          </span>
        </div>

        {trend && (
          <div className="mt-3 flex items-center gap-1.5">
            <span
              className={cn(
                "text-[10px] font-bold px-2.5 py-0.5 rounded-full shrink-0 uppercase tracking-wider border",
                trendType === 'positive' && "bg-[#34A853]/10 text-[#34A853] border-[#34A853]/10",
                trendType === 'negative' && "bg-[#EA4335]/10 text-[#EA4335] border-[#EA4335]/10",
                trendType === 'neutral' && "bg-muted text-muted-foreground border-border"
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
