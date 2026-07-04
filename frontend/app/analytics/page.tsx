"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CalendarDays, MessageCircle, Users, Utensils } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { api } from "@/lib/api";
import type { AdminAnalytics, Conversation, RuntimeEvent } from "@/types/api";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [errors, setErrors] = useState(0);
  useEffect(() => {
    void api.analytics().then(setAnalytics);
    void api.conversations().then(setConversations);
    void api.events().then((value) => setEvents(value.events));
    void api.errors().then((value) => setErrors(value.length));
  }, []);
  const intents = conversations.reduce<Record<string, number>>((acc, item) => {
    const key = item.intent ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Analytics Dashboard</h1><p className="text-sm text-muted-foreground">Operational SaaS metrics from local platform data.</p></div>
      <div className="grid gap-3 md:grid-cols-5">
        <StatCard label="Reservations" value={analytics?.reservations ?? "—"} icon={CalendarDays} />
        <StatCard label="Customers" value={analytics?.customers ?? "—"} icon={Users} />
        <StatCard label="Covers" value={analytics?.covers ?? "—"} icon={Utensils} />
        <StatCard label="AI Conversations" value={conversations.length} icon={MessageCircle} />
        <StatCard label="Errors" value={errors} icon={AlertTriangle} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card><CardHeader><CardTitle>Intent Mix</CardTitle></CardHeader><CardContent className="space-y-2">
          {Object.entries(intents).map(([intent, count]) => <div key={intent} className="flex justify-between rounded-md border p-3 text-sm"><span>{intent}</span><span>{count}</span></div>)}
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Runtime Events</CardTitle></CardHeader><CardContent><pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(events.slice(0, 20), null, 2)}</pre></CardContent></Card>
      </div>
    </div>
  );
}
