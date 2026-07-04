"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Bot,
  CalendarDays,
  ChartNoAxesCombined,
  Gauge,
  LayoutTemplate,
  MessageSquareText,
  Plug,
  Palette,
  Settings,
  Sparkles,
  Database,
  Workflow,
  Mic,
  ServerCog,
  Search,
  HelpCircle,
  Lightbulb,
  Sun,
  Moon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const nav = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/reservations", label: "Reservations", icon: CalendarDays },
  { href: "/knowledge", label: "Knowledge Base", icon: Database },
  { href: "/rag", label: "RAG Pipeline", icon: Database },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
  { href: "/prompt-studio", label: "Prompt Studio", icon: Sparkles },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { href: "/settings", label: "AI Settings", icon: Settings },
  { href: "/ollama", label: "Ollama Manager", icon: ServerCog },
  { href: "/playground", label: "Playground", icon: Sparkles },
  { href: "/voice", label: "Browser Voice", icon: Mic },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/branding", label: "Branding", icon: Palette },
  { href: "/plugins", label: "Plugins", icon: Plug },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-14 flex-col border-r bg-card lg:flex">
        <div className="flex h-14 items-center justify-center border-b shrink-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-md">
            <img src="/logo.png" alt="AgVoiceX Logo" className="h-6 w-6 object-contain" />
          </div>
        </div>
        <nav className="flex-1 space-y-2 p-2 overflow-y-auto mt-2">
          {nav.map((item) => {
            const active = pathname === item.href;
            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-md transition-colors",
                      active ? "bg-primary/20 text-emerald-500" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={10}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </nav>
      </aside>
      <main className="lg:pl-14 flex flex-col min-h-screen">
        {/* Top Navbar matching the image */}
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">AgVoiceX</span>
            <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">PRO</span>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-xs font-medium text-muted-foreground hover:text-foreground hidden sm:block">
              Feedback
            </button>
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search..."
                className="h-8 w-48 lg:w-64 rounded-md border border-border bg-muted/30 pl-8 pr-12 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:bg-background"
              />
              <div className="absolute right-1.5 top-1.5 flex items-center justify-center rounded border border-border bg-background px-1 text-[10px] font-medium text-muted-foreground shadow-sm">
                <span className="text-xs">⌘</span>K
              </div>
            </div>
            
            <button 
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Toggle theme"
            >
              <Sun className="h-4 w-4 hidden dark:block" />
              <Moon className="h-4 w-4 block dark:hidden" />
            </button>

            <button className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground">
              <HelpCircle className="h-4 w-4" />
            </button>
            <button className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground">
              <Lightbulb className="h-4 w-4" />
            </button>
            <div className="h-8 w-8 overflow-hidden rounded-full border border-border">
              <img
                src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"
                alt="Avatar"
                className="h-full w-full object-cover bg-muted"
              />
            </div>
          </div>
        </header>
        <div className="flex-1 mx-auto w-full px-4 py-8 sm:px-6 lg:px-8 max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
