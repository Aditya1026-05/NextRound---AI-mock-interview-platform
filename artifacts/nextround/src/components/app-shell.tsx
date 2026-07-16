import { Sidebar, LayoutDashboard, Code2, Users, Settings, LogOut, PanelLeft, Search, Bell } from "lucide-react"
import { Link, useLocation } from "wouter"
import { cn } from "@/lib/utils"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { useState } from "react"
import { ThemeToggle } from "./theme-toggle"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { motion, AnimatePresence } from "framer-motion"

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Code2, label: "Practice", href: "/practice" },
  { icon: Users, label: "Sessions", href: "/sessions/example" },
  { icon: Settings, label: "Settings", href: "/settings" },
  { icon: Sidebar, label: "Design System", href: "/design-system" },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const [location] = useLocation()
  const [isSidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen bg-secondary flex flex-col md:flex-row">
      {/* Mobile Navbar */}
      <div className="md:hidden flex items-center justify-between p-4 bg-background border-b z-20 sticky top-0">
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!isSidebarOpen)}>
            <PanelLeft className="h-5 w-5" />
          </Button>
          <span className="font-bold text-lg tracking-tight">NextRound</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>

      {/* Desktop Sidebar / Mobile Drawer */}
      <AnimatePresence>
        {(isSidebarOpen || window.innerWidth >= 768) && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: isSidebarOpen ? 260 : 72, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className={cn(
              "fixed inset-y-0 left-0 z-30 flex flex-col bg-background border-r transform transition-transform duration-300 md:relative md:translate-x-0 overflow-hidden",
              !isSidebarOpen ? "-translate-x-full md:translate-x-0" : "translate-x-0"
            )}
          >
            <div className="h-16 flex items-center px-4 border-b shrink-0 overflow-hidden">
              <div className="flex items-center gap-1.5 w-full">
                <img 
                  src="/logo.png" 
                  alt="NextRound Logo" 
                  className="w-8 h-8 object-contain shrink-0 select-none"
                />
                <AnimatePresence>
                  {isSidebarOpen && (
                    <motion.span 
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="font-bold text-lg tracking-tight whitespace-nowrap"
                    >
                      NextRound
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <div className="flex-1 py-6 px-3 flex flex-col gap-2 overflow-y-auto overflow-x-hidden">
              {NAV_ITEMS.map((item) => {
                const isActive = location.startsWith(item.href) || 
                               (item.href.includes('/sessions') && location.startsWith('/sessions'))
                return (
                  <Link key={item.href} href={item.href}>
                    <div
                      className={cn(
                        "flex items-center gap-3 px-4 py-2.5 rounded-full text-sm font-medium transition-colors cursor-pointer whitespace-nowrap",
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                      )}
                    >
                      <item.icon className="h-5 w-5 shrink-0" strokeWidth={isActive ? 2.5 : 2} />
                      <AnimatePresence>
                        {isSidebarOpen && (
                          <motion.span 
                            initial={{ opacity: 0, width: 0 }} 
                            animate={{ opacity: 1, width: "auto" }} 
                            exit={{ opacity: 0, width: 0 }}
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </div>
                  </Link>
                )
              })}
            </div>

            {/* Collapse toggle at bottom for desktop */}
            <div className="p-4 border-t hidden md:flex items-center justify-center shrink-0">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!isSidebarOpen)}
                className="w-full flex justify-center"
              >
                <PanelLeft className="h-5 w-5 text-muted-foreground" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Desktop Header */}
        <header className="h-16 hidden md:flex items-center justify-between px-8 bg-background/80 backdrop-blur-sm border-b sticky top-0 z-10">
          <div className="w-96 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Search questions, sessions..." 
              className="pl-9 h-10 bg-secondary/50 border-transparent focus:bg-background focus:border-input" 
            />
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="text-muted-foreground relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full" />
            </Button>
            <ThemeToggle />
            <UserMenu />
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-4 md:p-8">
          <div className="max-w-[1600px] mx-auto w-full">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </div>
        </main>
      </div>

      {/* Mobile Sidebar Overlay */}
      {!isSidebarOpen && window.innerWidth < 768 && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-20 md:hidden"
          onClick={() => setSidebarOpen(true)}
        />
      )}
    </div>
  )
}

function UserMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-9 w-9 rounded-full ml-2 overflow-hidden border border-border">
          <Avatar className="h-full w-full">
            <AvatarImage src="https://github.com/shadcn.png" alt="@user" />
            <AvatarFallback>EN</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">Software Engineer</p>
            <p className="text-xs leading-none text-muted-foreground">
              engineer@example.com
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild className="text-destructive focus:text-destructive cursor-pointer">
          <Link href="/login" className="flex items-center w-full">
            <LogOut className="mr-2 h-4 w-4" />
            <span>Log out</span>
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
