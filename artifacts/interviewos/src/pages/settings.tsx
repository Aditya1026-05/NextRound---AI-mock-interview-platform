import * as React from "react"
import { Monitor, User, Bell, Shield, Paintbrush } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ThemeToggle } from "@/components/theme-toggle"
import { Separator } from "@/components/ui/separator"

export default function Settings() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tighter text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-2 text-lg">Manage your account settings and preferences.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar Navigation */}
        <nav className="w-full md:w-64 space-y-1">
          <Button variant="secondary" className="w-full justify-start rounded-full">
            <User className="mr-2 h-4 w-4" /> Account
          </Button>
          <Button variant="ghost" className="w-full justify-start rounded-full text-muted-foreground hover:text-foreground hover:bg-secondary">
            <Paintbrush className="mr-2 h-4 w-4" /> Appearance
          </Button>
          <Button variant="ghost" className="w-full justify-start rounded-full text-muted-foreground hover:text-foreground hover:bg-secondary">
            <Bell className="mr-2 h-4 w-4" /> Notifications
          </Button>
          <Button variant="ghost" className="w-full justify-start rounded-full text-muted-foreground hover:text-foreground hover:bg-secondary">
            <Shield className="mr-2 h-4 w-4" /> Security
          </Button>
        </nav>

        {/* Content Area */}
        <div className="flex-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>Update your personal information.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Display Name</Label>
                <Input id="name" defaultValue="Alex Engineer" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" defaultValue="alex@example.com" />
              </div>
              <div className="pt-4">
                <Button>Save Changes</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize how InterviewOS looks on your device.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium">Theme</h4>
                  <p className="text-sm text-muted-foreground">Select light or dark mode.</p>
                </div>
                <ThemeToggle />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium">Reduce Motion</h4>
                  <p className="text-sm text-muted-foreground">Disable subtle animations.</p>
                </div>
                <Button variant="outline" size="sm">Enabled</Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-destructive/20 bg-destructive/5">
            <CardHeader>
              <CardTitle className="text-destructive">Danger Zone</CardTitle>
              <CardDescription>Irreversible actions for your account.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive">Delete Account</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
