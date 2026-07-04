"use client";

import Link from "next/link";
import Image from "next/image";
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
  Search,
  Sun,
  Moon,
  AudioLines,
  BookOpenText,
  SlidersHorizontal,
} from "lucide-react";

import { N8nIcon, OllamaIcon, QdrantIcon } from "@/components/brand-icons";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const navTop = [
  { href: "/", label: "Live Voice", icon: AudioLines },
];

const navMiddle = [
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/reservations", label: "Reservations", icon: CalendarDays },
  { href: "/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/prompt-studio", label: "Prompts", icon: Sparkles },
  { href: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
];

const navBottom = [
  { href: "/settings", label: "Settings", icon: SlidersHorizontal },
  { href: "/knowledge", label: "Knowledge", icon: BookOpenText },
  { href: "/branding", label: "Branding", icon: Palette },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  const renderNavGroup = (items: typeof navTop) => (
    <div className="flex flex-col gap-1">
      {items.map((item) => {
        const active = pathname === item.href;
        return (
          <Tooltip key={item.href}>
            <TooltipTrigger asChild>
              <Link
                href={item.href}
                className={cn(
                  "relative mx-auto flex h-10 w-10 items-center justify-center transition-colors",
                  active 
                    ? "text-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded-r-md" 
                    : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800",
                )}
              >
                {active && (
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-600 rounded-r-full" />
                )}
                <item.icon className="h-5 w-5" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={10}>
              {item.label}
            </TooltipContent>
          </Tooltip>
        );
      })}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0F1115]">
      <aside className="fixed inset-y-0 left-0 hidden w-[68px] flex-col border-r border-gray-200 dark:border-[#2A2E38] bg-white dark:bg-[#1A1D24] lg:flex z-20">
        <div className="flex h-16 items-center justify-center border-b border-gray-200 dark:border-[#2A2E38] shrink-0">
          <Link href="/" className="flex items-center justify-center rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Image src="/logo.png" alt="Logo" width={48} height={24} className="h-8 w-14 object-contain" priority />
          </Link>
        </div>
        
        <nav className="flex-1 flex flex-col p-2 overflow-y-auto overflow-x-hidden no-scrollbar">
          <div className="mt-2 mb-4">
            {renderNavGroup(navTop)}
          </div>
          
          <hr className="border-t border-gray-200 dark:border-[#2A2E38] mx-2" />
          
          <div className="my-4">
            {renderNavGroup(navMiddle)}
          </div>
          
          <div className="mt-auto pt-4 flex flex-col gap-4 border-t border-gray-200 dark:border-[#2A2E38]">
            {renderNavGroup(navBottom)}
            
            <div className="mt-2 flex items-center justify-center pb-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="flex h-10 w-10 items-center justify-center rounded-full bg-[#2563EB] text-white hover:bg-[#1E40AF] transition-colors shadow-sm">
                    <span className="text-[13px] font-semibold">TM</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={10}>
                  <div className="flex flex-col">
                    <span className="font-medium">Tahsin Mert</span>
                    <span className="text-xs text-gray-400">Admin</span>
                  </div>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </nav>
      </aside>
      
      <main className="lg:pl-[68px] flex flex-col min-h-screen relative">
        <div className="flex-1 w-full mx-auto pb-8 bg-gray-50 dark:bg-[#0F1115]">
          {children}
        </div>
      </main>
    </div>
  );
}
