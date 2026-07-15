import React, { useEffect, useState } from 'react';
import { useUIStore } from '@/store/useUIStore';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { FileUp, Eye, Sparkles, CheckCircle2, ShieldAlert } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function ResumeIntelligence() {
  const { setBreadcrumbs } = useUIStore();
  const [fileName, setFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    setBreadcrumbs(['Dashboard', 'Resume Intelligence']);
  }, [setBreadcrumbs]);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
    }, 1500);
  };

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto space-y-6 select-none">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Resume Intelligence</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Analyze your CV with deep AI matching algorithms to evaluate strength, find omissions, and generate custom target interview templates.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Upload Card */}
          <Card className="md:col-span-2 hover:border-foreground/10 transition-colors">
            <CardHeader className="p-6">
              <CardTitle className="text-base font-bold">Upload Resume</CardTitle>
              <CardDescription className="text-xs">Upload your PDF or Word document to parse capabilities.</CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              <div className="border border-dashed border-border rounded-xl p-8 text-center bg-muted/20 flex flex-col items-center justify-center space-y-4">
                <div className="p-3 rounded-full bg-foreground/5 text-foreground shrink-0 border border-border">
                  <FileUp className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold">Drag & drop your file here, or click to browse</p>
                  <p className="text-[10px] text-muted-foreground">PDF, DOCX up to 10MB</p>
                </div>
                <Input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleUpload}
                  className="hidden"
                  id="resume-input"
                />
                <Button 
                  asChild 
                  variant="outline" 
                  size="sm" 
                  className="rounded-full text-xs font-semibold"
                >
                  <label htmlFor="resume-input" className="cursor-pointer">
                    Select File
                  </label>
                </Button>
              </div>

              {fileName && (
                <div className="mt-4 p-3 bg-foreground/5 border border-border rounded-lg flex items-center justify-between text-xs font-medium">
                  <span className="truncate max-w-[80%]">{fileName}</span>
                  {isUploading ? (
                    <span className="text-violet-600 dark:text-violet-400 animate-pulse uppercase tracking-wider text-[9px] font-bold">Analyzing...</span>
                  ) : (
                    <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1 text-[9px] font-bold"><CheckCircle2 className="h-4.5 w-4.5" /> PARSED</span>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Metrics summary */}
          <Card className="hover:border-foreground/10 transition-colors flex flex-col justify-between">
            <CardHeader className="p-6">
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Sparkles className="h-4.5 w-4.5 text-violet-500" />
                AI Persona Profile
              </CardTitle>
              <CardDescription className="text-xs">Extracted resume insights.</CardDescription>
            </CardHeader>
            <CardContent className="p-6 pt-0 space-y-4 text-xs">
              <div className="space-y-1">
                <p className="font-semibold text-muted-foreground">Primary Skill Focus</p>
                <p className="font-bold text-foreground">React, TypeScript, System Architecture</p>
              </div>
              <div className="space-y-1">
                <p className="font-semibold text-muted-foreground">Years of Experience</p>
                <p className="font-bold text-foreground">6.5 Years (Senior Grade)</p>
              </div>
              <div className="space-y-1">
                <p className="font-semibold text-muted-foreground">Resume Score</p>
                <p className="font-bold text-emerald-600 dark:text-emerald-400">89/100 (Strong)</p>
              </div>
            </CardContent>
            <CardFooter className="p-6 border-t border-border flex items-center justify-end select-none">
              <Button size="sm" variant="ghost" className="text-xs font-semibold text-muted-foreground hover:text-foreground">
                <Eye className="h-4 w-4 mr-1.5" />
                View Report
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
export { ResumeIntelligence };
