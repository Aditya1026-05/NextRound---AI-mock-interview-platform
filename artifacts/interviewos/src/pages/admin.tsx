import React, { useEffect } from 'react';
import { useUIStore } from '@/store/useUIStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { AdminLayout } from '@/components/layouts/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldCheck, Database, Key, Server, Cpu } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Admin() {
  const { setBreadcrumbs } = useUIStore();

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Root Administrator']);
  }, [setBreadcrumbs]);

  return (
    <DashboardLayout>
      <AdminLayout>
        <div className="space-y-6 select-none">
          <div>
            <h3 className="text-lg font-bold text-foreground">Platform Infrastructure</h3>
            <p className="text-muted-foreground text-xs">Verify AI cluster load, sync active records, and audit license checks.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="hover:border-foreground/10 transition-colors">
              <CardHeader className="p-4">
                <CardTitle className="text-xs font-bold flex items-center gap-1.5 text-foreground">
                  <Server className="h-4 w-4 text-muted-foreground" />
                  Cluster Health
                </CardTitle>
                <CardDescription className="text-[10px]">Active inference pods online.</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Active Sessions:</span>
                  <span className="font-semibold text-foreground">412 Users</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Inference Load:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">14% (Optimized)</span>
                </div>
              </CardContent>
            </Card>

            <Card className="hover:border-foreground/10 transition-colors">
              <CardHeader className="p-4">
                <CardTitle className="text-xs font-bold flex items-center gap-1.5 text-foreground">
                  <Database className="h-4 w-4 text-muted-foreground" />
                  Sync Status
                </CardTitle>
                <CardDescription className="text-[10px]">PostgreSQL synchronization queues.</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Pending Syncs:</span>
                  <span className="font-semibold text-foreground">0 records</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Last Database Push:</span>
                  <span className="font-semibold text-foreground">2 mins ago</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="border-t border-border pt-4 flex items-center justify-end select-none">
            <Button size="sm" className="rounded-md text-[10px] gap-1.5 bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-800 text-white border-0 font-semibold h-8">
              Trigger Server Hard Reboot
            </Button>
          </div>
        </div>
      </AdminLayout>
    </DashboardLayout>
  );
}
export { Admin };
