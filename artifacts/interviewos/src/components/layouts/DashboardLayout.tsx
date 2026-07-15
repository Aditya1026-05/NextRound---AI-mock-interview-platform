import React from 'react';
import { Link, useLocation } from 'wouter';
import { 
  LayoutDashboard, 
  Code2, 
  History, 
  LineChart, 
  Settings, 
  Map, 
  ShieldAlert, 
  Search, 
  Bell, 
  PanelLeft, 
  User, 
  ChevronRight, 
  LogOut,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemeToggle } from '@/components/theme-toggle';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { motion, AnimatePresence } from 'framer-motion';

const SIDEBAR_ITEMS = [
  { group: 'Overview', items: [
    { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
    { icon: LineChart, label: 'Analytics', href: '/analytics' },
    { icon: Map, label: 'Learning Roadmap', href: '/roadmap' },
  ]},
  { group: 'Preparation', items: [
    { icon: Code2, label: 'Practice Hub', href: '/practice' },
    { icon: History, label: 'Session History', href: '/interviews/history' },
  ]},
  { group: 'System', items: [
    { icon: Settings, label: 'Settings', href: '/settings' },
    { icon: ShieldAlert, label: 'Admin', href: '/admin', roles: ['admin', 'enterprise'] }
  ]}
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const { sidebarOpen, toggleSidebar, breadcrumbs } = useUIStore();
  const { profile, logout } = useUserStore();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row text-foreground">
      {/* Sidebar Overlay for Mobile */}
      {!sidebarOpen && (
        <div 
          className="fixed inset-0 bg-background/40 backdrop-blur-sm z-40 md:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <motion.aside
        animate={{ width: sidebarOpen ? 260 : 72 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-card border-r border-border shrink-0 overflow-hidden md:relative md:translate-x-0",
          !sidebarOpen && "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center px-4 border-b border-border shrink-0 justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-foreground text-background w-8 h-8 rounded-md flex items-center justify-center font-semibold text-sm shadow-sm shrink-0">
              io
            </div>
            {sidebarOpen && (
              <span className="font-semibold text-base tracking-tight whitespace-nowrap">
                InterviewOS
              </span>
            )}
          </div>
          {sidebarOpen && (
            <Button variant="ghost" size="icon" onClick={toggleSidebar} className="h-8 w-8 hidden md:inline-flex">
              <PanelLeft className="h-4 w-4 text-muted-foreground" />
            </Button>
          )}
        </div>

        {/* Sidebar Nav */}
        <div className="flex-1 py-4 px-3 flex flex-col gap-6 overflow-y-auto select-none">
          {SIDEBAR_ITEMS.map((group, gIdx) => {
            // Check if group is visible
            const filteredItems = group.items.filter(item => {
              if (item.roles && profile) {
                return item.roles.includes(profile.subscriptionTier);
              }
              return true;
            });

            if (filteredItems.length === 0) return null;

            return (
              <div key={gIdx} className="flex flex-col gap-1">
                {sidebarOpen && (
                  <span className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest px-4 mb-1">
                    {group.group}
                  </span>
                )}
                {filteredItems.map((item) => {
                  const isActive = location === item.href || (item.href !== '/dashboard' && location.startsWith(item.href));
                  return (
                    <Link key={item.href} href={item.href}>
                      <span
                        className={cn(
                          "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer whitespace-nowrap",
                          isActive
                            ? "bg-foreground/5 text-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        )}
                      >
                        <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")} />
                        {sidebarOpen && (
                          <span className="flex-1">{item.label}</span>
                        )}
                      </span>
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* User Workspace Profile bottom footer */}
        <div className="p-3 border-t border-border shrink-0">
          {profile && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className={cn(
                  "flex items-center gap-3 p-2 rounded-md hover:bg-muted cursor-pointer transition-colors overflow-hidden",
                  !sidebarOpen && "justify-center"
                )}>
                  <Avatar className="h-8 w-8 border border-border">
                    <AvatarImage src={profile.avatar} alt={profile.name} />
                    <AvatarFallback>{profile.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                  {sidebarOpen && (
                    <div className="flex-1 text-left min-w-0">
                      <p className="text-xs font-semibold truncate leading-none mb-1 text-foreground">
                        {profile.name}
                      </p>
                      <p className="text-[10px] text-muted-foreground truncate leading-none capitalize">
                        {profile.subscriptionTier} Tier
                      </p>
                    </div>
                  )}
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-52 ml-2" align="start" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{profile.name}</p>
                    <p className="text-xs leading-none text-muted-foreground">{profile.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="flex items-center w-full cursor-pointer">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </motion.aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-4 md:px-8 bg-background border-b border-border sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={toggleSidebar} className="h-9 w-9">
              <PanelLeft className="h-4 w-4 text-foreground" />
            </Button>
            <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={idx}>
                  {idx > 0 && <ChevronRight className="h-3 w-3" />}
                  <span className={cn(idx === breadcrumbs.length - 1 && "text-foreground font-semibold")}>
                    {crumb}
                  </span>
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Minimal Premium Search */}
            <div className="relative w-48 md:w-64 hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input 
                placeholder="Search resources..." 
                className="pl-9 h-8 bg-muted/65 border-transparent text-xs hover:bg-muted focus:bg-background focus:border-border rounded-full" 
              />
            </div>
            
            <ThemeToggle />
            
            <Button variant="outline" size="sm" className="rounded-full gap-1.5 h-8 text-xs font-semibold bg-gradient-to-r from-violet-600/10 to-indigo-600/10 hover:from-violet-600/15 hover:to-indigo-600/15 text-violet-700 dark:text-violet-300 border-violet-500/20">
              <Sparkles className="h-3.5 w-3.5" />
              AI Premium
            </Button>
          </div>
        </header>

        {/* Content Viewport */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-background/50">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
