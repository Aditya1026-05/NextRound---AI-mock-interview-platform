import React, { useEffect, useState } from 'react';
import { useUIStore } from '@/store/useUIStore';
import { useUserStore } from '@/store/useUserStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { SettingsLayout } from '@/components/layouts/SettingsLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sparkles, Key, CheckCircle2 } from 'lucide-react';

export default function Settings() {
  const { setBreadcrumbs } = useUIStore();
  const { profile, setProfile } = useUserStore();
  
  const [name, setName] = useState(profile?.name || '');
  const [role, setRole] = useState(profile?.targetRole || '');
  const [company, setCompany] = useState(profile?.targetCompany || '');

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Settings']);
  }, [setBreadcrumbs]);

  const handleSave = () => {
    setProfile({
      name,
      targetRole: role,
      targetCompany: company,
    });
  };

  return (
    <DashboardLayout>
      <SettingsLayout>
        <div className="space-y-6 select-none">
          <div>
            <h3 className="text-lg font-bold text-foreground">Profile Details</h3>
            <p className="text-muted-foreground text-xs">Manage your personal profile and job hunting parameters.</p>
          </div>

          <div className="space-y-4 max-w-md">
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-xs font-semibold">Full Name</Label>
              <Input 
                id="name" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="target-role" className="text-xs font-semibold">Target Position</Label>
              <Input 
                id="target-role" 
                value={role} 
                onChange={(e) => setRole(e.target.value)} 
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="target-company" className="text-xs font-semibold">Target Company</Label>
              <Input 
                id="target-company" 
                value={company} 
                onChange={(e) => setCompany(e.target.value)} 
                className="h-9 text-xs"
              />
            </div>
          </div>

          {/* SaaS Plan tier */}
          <div className="border border-border bg-muted/20 p-4 rounded-xl max-w-md flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-xs font-bold text-foreground">SaaS Subscription Plan</p>
              <p className="text-[10px] text-muted-foreground leading-none">Pro Developer Plan — Unlimited Evaluations</p>
            </div>
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-violet-700 dark:text-violet-300 bg-violet-500/10 px-2.5 py-0.5 rounded-full select-none">
              <Sparkles className="h-3 w-3 animate-pulse" />
              ACTIVE PRO
            </span>
          </div>

          <div className="border-t border-border pt-4 flex items-center justify-end max-w-md select-none">
            <Button 
              onClick={handleSave}
              className="rounded-md text-xs bg-foreground text-background hover:bg-foreground/90 h-9 font-semibold"
            >
              Save Profile Changes
            </Button>
          </div>
        </div>
      </SettingsLayout>
    </DashboardLayout>
  );
}
export { Settings };
