import * as React from "react"
import { AlertCircle } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/empty-state"

export default function DesignSystem() {
  return (
    <div className="space-y-12 max-w-5xl mx-auto pb-20">
      <div>
        <h1 className="text-5xl font-bold tracking-tighter text-foreground">Design System</h1>
        <p className="text-muted-foreground mt-2 text-xl">Living style guide for InterviewOS UI primitives.</p>
      </div>

      {/* Colors */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Color Palette</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ColorSwatch name="Background" variable="bg-background" />
          <ColorSwatch name="Secondary" variable="bg-secondary" />
          <ColorSwatch name="Card" variable="bg-card" />
          <ColorSwatch name="Border" variable="bg-border" />
          <ColorSwatch name="Primary (Blue)" variable="bg-primary" textClass="text-primary-foreground" />
          <ColorSwatch name="Destructive (Red)" variable="bg-destructive" textClass="text-destructive-foreground" />
          <ColorSwatch name="Success (Green)" variable="bg-[hsl(var(--success))]" textClass="text-primary-foreground" />
          <ColorSwatch name="Warning (Yellow)" variable="bg-[hsl(var(--warning))]" textClass="text-foreground" />
        </div>
      </section>

      {/* Typography */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Typography</h2>
        <Card>
          <CardContent className="space-y-6 pt-6">
            <div>
              <h1 className="text-4xl font-bold tracking-tighter">Heading 1</h1>
              <p className="text-sm text-muted-foreground mt-1">Inter Bold, 36px (text-4xl)</p>
            </div>
            <div>
              <h2 className="text-3xl font-semibold tracking-tight">Heading 2</h2>
              <p className="text-sm text-muted-foreground mt-1">Inter Semibold, 30px (text-3xl)</p>
            </div>
            <div>
              <h3 className="text-2xl font-semibold tracking-tight">Heading 3</h3>
              <p className="text-sm text-muted-foreground mt-1">Inter Semibold, 24px (text-2xl)</p>
            </div>
            <div>
              <p className="text-lg text-foreground">
                Base text. The quick brown fox jumps over the lazy dog. This is used for primary body copy across the application.
              </p>
              <p className="text-sm text-muted-foreground mt-1">Inter Regular, 18px (text-lg)</p>
            </div>
            <div>
              <p className="text-base text-muted-foreground">
                Small text. Used for secondary information, descriptions, and metadata.
              </p>
              <p className="text-sm text-muted-foreground mt-1">Inter Regular, 16px (text-base)</p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Buttons */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Buttons</h2>
        <Card>
          <CardContent className="flex flex-wrap gap-4 pt-6">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Primary</p>
              <Button>Primary Action</Button>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Secondary</p>
              <Button variant="secondary">Secondary Action</Button>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Outline</p>
              <Button variant="outline">Outline Action</Button>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Ghost</p>
              <Button variant="ghost">Ghost Action</Button>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Destructive</p>
              <Button variant="destructive">Delete Item</Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Badges */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Badges</h2>
        <Card>
          <CardContent className="flex flex-wrap gap-4 pt-6">
            <Badge>Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="destructive">Destructive</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="info">Info</Badge>
          </CardContent>
        </Card>
      </section>

      {/* Inputs */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Inputs & Forms</h2>
        <Card>
          <CardContent className="space-y-4 pt-6 max-w-sm">
            <div className="space-y-2">
              <label className="text-sm font-medium">Standard Input</label>
              <Input placeholder="Placeholder text..." />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Disabled Input</label>
              <Input disabled placeholder="Disabled state" />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* States */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold border-b pb-2">Loading & Empty States</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Skeleton Loading</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-[200px]" />
                </div>
              </div>
              <Skeleton className="h-32 w-full rounded-xl" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Empty State</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState 
                title="No items found"
                description="Get started by creating your first item."
                action={{ label: "Create Item", onClick: () => {} }}
              />
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}

function ColorSwatch({ name, variable, textClass = "text-foreground" }: { name: string, variable: string, textClass?: string }) {
  return (
    <div className="border rounded-xl overflow-hidden shadow-sm">
      <div className={`h-24 ${variable} flex items-center justify-center`}>
        <span className={`text-sm font-medium opacity-0 hover:opacity-100 transition-opacity ${textClass}`}>
          {variable}
        </span>
      </div>
      <div className="p-3 bg-card border-t">
        <p className="text-sm font-semibold">{name}</p>
      </div>
    </div>
  )
}
