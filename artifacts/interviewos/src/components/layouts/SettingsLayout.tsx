import React from 'react';
import { Link, useLocation } from 'wouter';
import { User, CreditCard, Bell, Key, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

const SETTINGS_TABS = [
  { label: 'Profile & Preferences', href: '/settings/profile', icon: User },
  { label: 'Billing & Plans', href: '/settings/billing', icon: CreditCard },
  { label: 'Notifications', href: '/settings/notifications', icon: Bell },
  { label: 'Developer & API Keys', href: '/settings/developer', icon: Key },
  { label: 'Security & Access', href: '/settings/security', icon: ShieldCheck },
];

export function SettingsLayout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="space-y-6">
      {/* Header title */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Account Settings</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Configure your personal details, AI interview configs, APIs, and plans.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Settings Tab Sidebar Navigation */}
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="flex flex-row lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible py-1">
            {SETTINGS_TABS.map((tab) => {
              // active if exact or starts with (excluding edge cases)
              const isActive = location === tab.href || 
                (tab.href === '/settings' && location === '/settings') ||
                (tab.href !== '/settings/profile' && location === tab.href);

              return (
                <Link key={tab.href} href={tab.href}>
                  <span
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer whitespace-nowrap",
                      isActive
                        ? "bg-foreground/5 text-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <tab.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")} />
                    <span>{tab.label}</span>
                  </span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Tab Viewport */}
        <div className="flex-1 bg-card border border-border rounded-xl p-6 shadow-sm min-w-0">
          {children}
        </div>
      </div>
    </div>
  );
}
