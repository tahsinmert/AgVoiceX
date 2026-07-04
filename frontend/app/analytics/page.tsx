"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CalendarDays, MessageCircle, RefreshCw, Users } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { AdminAnalytics, AdminError, Conversation, Reservation, RuntimeEvent } from "@/types/api";

const COLORS = ["#2563EB", "#059669", "#D97706", "#DC2626", "#7C3AED", "#64748B"];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [errors, setErrors] = useState<AdminError[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    void Promise.all([
      api.analytics().then(setAnalytics),
      api.reservations().then(setReservations),
      api.conversations().then(setConversations),
      api.events().then((value) => setEvents(value.events)),
      api.errors().then(setErrors),
    ]).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const today = new Date().toISOString().slice(0, 10);

  const hourlyData = useMemo(() => {
    return Array.from({ length: 24 }, (_, hour) => {
      const key = `${String(hour).padStart(2, "0")}:00`;
      const reservationCount = reservations.filter((item) => {
        if (item.reservation_date !== today) return false;
        return Number((item.reservation_time || "00:00").slice(0, 2)) === hour;
      }).length;
      const conversationCount = conversations.filter((item) => {
        const created = new Date(item.created_at);
        return !Number.isNaN(created.getTime()) && created.toISOString().slice(0, 10) === today && created.getHours() === hour;
      }).length;
      return { time: key, reservations: reservationCount, conversations: conversationCount };
    });
  }, [conversations, reservations, today]);

  const intentData = useMemo(() => {
    const counts = conversations.reduce<Record<string, number>>((acc, item) => {
      const key = item.intent || "unknown";
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [conversations]);

  const todayReservations = reservations.filter((item) => item.reservation_date === today && item.status !== "cancelled");
  const activeReservations = reservations.filter((item) => item.status !== "cancelled");

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Live operational metrics calculated from backend records.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <Metric icon={CalendarDays} label="Reservations" value={analytics?.reservations ?? reservations.length} />
        <Metric icon={Users} label="Customers" value={analytics?.customers ?? 0} />
        <Metric icon={Users} label="Covers" value={analytics?.covers ?? activeReservations.reduce((sum, item) => sum + item.people, 0)} />
        <Metric icon={MessageCircle} label="Conversations" value={conversations.length} />
        <Metric icon={AlertTriangle} label="Errors" value={errors.length} tone={errors.length > 0 ? "danger" : "default"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <Card>
          <CardHeader><CardTitle>Activity Today</CardTitle></CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyData} margin={{ top: 10, right: 16, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="analyticsReservations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="analyticsConversations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.22} />
                    <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="conversations" stroke="#059669" fill="url(#analyticsConversations)" strokeWidth={2} />
                <Area type="monotone" dataKey="reservations" stroke="#2563EB" fill="url(#analyticsReservations)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Intent Mix</CardTitle></CardHeader>
          <CardContent>
            {intentData.length === 0 ? (
              <EmptyState title="No conversation intents yet" />
            ) : (
              <>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={intentData} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82}>
                        {intentData.map((entry, index) => <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-2">
                  {intentData.map((intent, index) => (
                    <div key={intent.name} className="flex items-center justify-between rounded-md border p-2 text-sm">
                      <span className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                        {intent.name}
                      </span>
                      <Badge>{intent.value}</Badge>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Today&apos;s Reservation Status</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {todayReservations.length === 0 ? <EmptyState title="No reservations today" /> : todayReservations.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                <div>
                  <p className="font-medium">{item.customer_name ?? `Reservation #${item.id}`}</p>
                  <p className="text-muted-foreground">{item.reservation_time.slice(0, 5)} · {item.people} guests</p>
                </div>
                <Badge>{item.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Runtime Events</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {events.length === 0 ? <EmptyState title="No runtime events yet" /> : events.slice(0, 12).map((event) => (
              <div key={event.id} className="rounded-md border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{event.type}</p>
                  <span className="text-xs text-muted-foreground">{new Date(event.created_at).toLocaleString()}</span>
                </div>
                <pre className="mt-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs">{JSON.stringify(event.payload, null, 2)}</pre>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone = "default" }: { icon: typeof CalendarDays; label: string; value: number; tone?: "default" | "danger" }) {
  return (
    <div className={`flex items-center gap-3 rounded-lg border bg-card p-4 ${tone === "danger" ? "border-red-200 bg-red-50" : ""}`}>
      <div className={`flex h-10 w-10 items-center justify-center rounded-md ${tone === "danger" ? "bg-red-100 text-red-700" : "bg-primary/10 text-primary"}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </div>
    </div>
  );
}
