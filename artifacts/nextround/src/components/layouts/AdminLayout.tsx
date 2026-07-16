import React from 'react';
import { Link, useLocation } from 'wouter';
import { Users, BarChart3, Settings, ShieldCheck, Database, Key } from 'lucide-react';
import { cn } from '@/lib/utils';

const ADMIN_TABS = [
  { label: 'Platform Users', href: '/admin/users', icon: Users },
  { label: 'System Analytics', href: '/admin/analytics', icon: BarChart3 },
  { label: 'Database & Sync', href: '/admin/database', icon: Database },
  { label: 'Security & Access', href: '/admin/security', icon: ShieldCheck },
];

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-destructive-foreground dark:text-red-400">Admin Control Panel</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Global system overrides, user tracking, platform health, database syncs, and license controls.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 px-3 py-1 rounded-md text-xs font-mono font-semibold select-none">
          <ShieldCheck className="h-4 w-4 animate-pulse" />
          <span>Root Authorization Active</span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="flex flex-row lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible py-1">
            {ADMIN_TABS.map((tab) => {
              const isActive = location === tab.href || (tab.href !== '/admin' && location.startsWith(tab.href));
              return (
                <Link key={tab.href} href={tab.href}>
                  <span
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer whitespace-nowrap",
                      isActive
                        ? "bg-red-500/10 text-red-600 dark:text-red-400 font-semibold"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <tab.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-red-600 dark:text-red-400" : "text-muted-foreground")} />
                    <span>{tab.label}</span>
                  </span>
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex-1 bg-card border border-border rounded-xl p-6 shadow-sm min-w-0">
          {children}
        </div>
      </div>
    </div>
  );
}
