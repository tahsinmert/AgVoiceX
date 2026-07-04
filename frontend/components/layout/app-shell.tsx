"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Bot,
  CalendarDays,
  ChartNoAxesCombined,
  LayoutTemplate,
  MessageSquareText,
  Plug,
  Palette,
  Sparkles,
  Database,
  Workflow,
  ServerCog,
  Search,
  Sun,
  Moon,
  AudioLines,
  BookOpenText,
  SlidersHorizontal,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const nav = [
  { href: "/", label: "Live Voice", icon: AudioLines },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/prompt-studio", label: "Prompts", icon: Sparkles },
  { href: "/settings", label: "Models", icon: SlidersHorizontal },
  { href: "/ollama", label: "Ollama", icon: ServerCog },
  { href: "/knowledge", label: "Knowledge", icon: BookOpenText },
  { href: "/reservations", label: "Reservations", icon: CalendarDays },
  { href: "/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/rag", label: "RAG", icon: Database },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
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
                      active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
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
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">AgVoiceX</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative hidden sm:block">
              <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search"
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
          </div>
        </header>
        <div className="flex-1 mx-auto w-full px-4 py-4 sm:px-6 lg:px-8 max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
