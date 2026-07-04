"use client";

import type React from "react";
import { useEffect, useState } from "react";
import {
  Activity,
  AudioLines,
  CalendarClock,
  CheckCircle2,
  Database,
  MessageSquareText,
  PhoneCall,
  Server,
  Sparkles,
} from "lucide-react";

import { VoiceClient } from "@/components/voice/voice-client";
import { api } from "@/lib/api";
import type { AdminAnalytics, Conversation, Health, Model, Reservation } from "@/types/api";

export default function VoiceConsolePage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    void Promise.all([
      api.health().then(setHealth).catch(() => setHealth(null)),
      api.models().then(setModels).catch(() => setModels([])),
      api.analytics().then(setAnalytics).catch(() => setAnalytics(null)),
      api.reservations().then(setReservations).catch(() => setReservations([])),
      api.conversations().then(setConversations).catch(() => setConversations([])),
    ]);
  }, []);

  const activeModel = models[0]?.name ?? "No model visible";
  const latestCalls = conversations.slice(0, 5);
  const upcomingReservations = reservations.slice(0, 5);

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <div className="min-h-[520px] rounded-lg border border-border bg-card p-5 sm:p-6">
          <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-500">
                <AudioLines className="h-3.5 w-3.5" />
                Local, unlimited voice agent
              </div>
              <h1 className="max-w-3xl text-3xl font-semibold tracking-normal text-foreground sm:text-4xl">
                Talk to your restaurant agent and let it handle reservations.
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                Speak naturally, confirm availability, create reservations, answer questions from knowledge, and store every conversation through the same local runtime.
              </p>
            </div>
            <div className="rounded-md border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-2 text-emerald-500">
                <CheckCircle2 className="h-4 w-4" />
                {health?.status === "ok" ? "Backend online" : "Checking backend"}
              </div>
              <div className="mt-1 max-w-52 truncate">Model: {activeModel}</div>
            </div>
          </div>

          <VoiceClient compact={false} />
        </div>

        <div className="space-y-4">
          <Metric icon={PhoneCall} label="Voice calls" value={conversations.length} detail="Stored conversation turns" />
          <Metric icon={CalendarClock} label="Reservations" value={reservations.length} detail="Created through tools or UI" />
          <Metric icon={Database} label="Customers" value={analytics?.customers ?? "—"} detail="Local PostgreSQL records" />
          <Metric icon={Server} label="Provider models" value={models.length} detail={activeModel} />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Panel title="Recent Voice/Chat Turns" icon={MessageSquareText}>
          {latestCalls.length ? (
            <div className="space-y-3">
              {latestCalls.map((item) => (
                <div key={item.id} className="rounded-md border border-border bg-background p-3">
                  <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
                    <span>{item.channel}</span>
                    <span>{item.intent ?? "unknown"}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm">{item.user_message}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.assistant_reply}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyLine text="No conversations yet. Start with the voice console above." />
          )}
        </Panel>

        <Panel title="Upcoming Reservations" icon={CalendarClock}>
          {upcomingReservations.length ? (
            <div className="space-y-3">
              {upcomingReservations.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border border-border bg-background p-3">
                  <div>
                    <p className="text-sm font-medium">{item.customer_name ?? `Reservation #${item.id}`}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.reservation_date} at {item.reservation_time} · {item.people} guests
                    </p>
                  </div>
                  <span className="rounded-full border border-border px-2 py-1 text-xs text-muted-foreground">{item.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyLine text="No reservations yet. Ask the voice agent to book a table." />
          )}
        </Panel>
      </section>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md border border-border bg-background text-emerald-500">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-sm font-medium">{label}</div>
      <div className="mt-1 truncate text-xs text-muted-foreground">{detail}</div>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof Sparkles;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-5 py-4">
        <Icon className="h-4 w-4 text-emerald-500" />
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function EmptyLine({ text }: { text: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-md border border-dashed border-border text-sm text-muted-foreground">
      {text}
    </div>
  );
}
