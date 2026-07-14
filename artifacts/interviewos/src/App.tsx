import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Switch, Router as WouterRouter } from 'wouter';

import { ThemeProvider } from '@/components/theme-provider';
import { AppShell } from '@/components/app-shell';

import Dashboard from '@/pages/dashboard';
import Practice from '@/pages/practice';
import SessionDetail from '@/pages/session-detail';
import Settings from '@/pages/settings';
import DesignSystem from '@/pages/design-system';
import NotFound from '@/pages/not-found';
import Auth from '@/pages/auth';

const queryClient = new QueryClient();

function ProtectedRouter() {
  return (
    <AppShell>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/practice" component={Practice} />
        <Route path="/sessions/:id" component={SessionDetail} />
        <Route path="/settings" component={Settings} />
        <Route path="/design-system" component={DesignSystem} />
        <Route component={NotFound} />
      </Switch>
    </AppShell>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="interviewos-theme">
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
