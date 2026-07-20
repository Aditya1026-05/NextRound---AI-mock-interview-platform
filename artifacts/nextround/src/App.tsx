import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Switch, Router as WouterRouter } from 'wouter';

import { ThemeProvider } from '@/components/theme-provider';
import { AppShell } from '@/components/app-shell';

import Dashboard from '@/pages/dashboard';
import Interviews from '@/pages/interviews';
import InterviewNew from '@/pages/interview-new';
import WaitingRoom from '@/pages/waiting-room';
import InterviewSession from '@/pages/interview-session';
import InterviewHistory from '@/pages/interview-history';
import Coding from '@/pages/coding';
import Behavioral from '@/pages/behavioral';
import SystemDesign from '@/pages/system-design';
import MachineLearning from '@/pages/ml';
import ResumeIntelligence from '@/pages/resume';
import Analytics from '@/pages/analytics';
import Roadmap from '@/pages/roadmap';
import Settings from '@/pages/settings';
import Admin from '@/pages/admin';
import DesignSystem from '@/pages/design-system';
import NotFound from '@/pages/not-found';
import Auth from '@/pages/auth';

import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { useUserStore } from '@/store/useUserStore';

const queryClient = new QueryClient();

function ProtectedRouter() {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const isLoading = useUserStore((state) => state.isLoading);
  const [location, setLocation] = useLocation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      setLocation('/login');
    }
  }, [isLoading, isAuthenticated, setLocation]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/interviews" component={Interviews} />
      <Route path="/interviews/new" component={InterviewNew} />
      <Route path="/interviews/waiting-room/:id" component={WaitingRoom} />
      <Route path="/interviews/session/:id" component={InterviewSession} />
      <Route path="/interviews/history" component={InterviewHistory} />
      <Route path="/coding" component={Coding} />
      <Route path="/behavioral" component={Behavioral} />
      <Route path="/system-design" component={SystemDesign} />
      <Route path="/ml" component={MachineLearning} />
      <Route path="/resume" component={ResumeIntelligence} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/roadmap" component={Roadmap} />
      <Route path="/settings" component={Settings} />
      <Route path="/settings/:sub" component={Settings} />
      <Route path="/admin" component={Admin} />
      <Route path="/admin/:sub" component={Admin} />
      <Route path="/design-system" component={DesignSystem} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const initialize = useUserStore((state) => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="nextround-theme">
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
            <Switch>
              <Route path="/login" component={Auth} />
              <Route path="/signup" component={Auth} />
              <Route component={ProtectedRouter} />
            </Switch>
          </WouterRouter>
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
