import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Switch, Router as WouterRouter } from 'wouter';

import { ThemeProvider } from '@/components/theme-provider';
import { AppShell } from '@/components/app-shell';

import Dashboard from '@/pages/dashboard';
import Interviews from '@/pages/interviews';
import InterviewNew from '@/pages/interview-new';
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

const queryClient = new QueryClient();

function ProtectedRouter() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/interviews" component={Interviews} />
      <Route path="/interviews/new" component={InterviewNew} />
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
