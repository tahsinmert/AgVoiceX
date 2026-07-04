"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, CalendarClock, MessageSquareText, RefreshCw, Search, User } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { formatDateTime } from "@/lib/utils";
import { api } from "@/lib/api";
import type { Conversation, RuntimeEvent } from "@/types/api";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    void Promise.all([
      api.conversations().then((data) => {
        setConversations(data);
        setSelectedId((current) => current ?? data[0]?.id ?? null);
      }),
      api.events().then((value) => setEvents(value.events)),
    ]).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return conversations;
    return conversations.filter((item) => [item.id, item.user_message, item.assistant_reply, item.intent, item.channel].join(" ").toLowerCase().includes(needle));
  }, [conversations, query]);

  const selected = filtered.find((item) => item.id === selectedId) ?? filtered[0] ?? null;
  const selectedEvents = selected ? events.filter((event) => event.conversation_id === selected.id) : [];

  return (
    <div className="flex h-[calc(100vh-6.5rem)] min-h-[620px] flex-col gap-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Conversations</h1>
          <p className="text-sm text-muted-foreground">Inspect real messages, intents, tool plans and runtime events.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          Refresh
        </Button>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[380px_minmax(0,1fr)]">
        <Card className="flex min-h-0 flex-col">
          <CardHeader>
            <CardTitle>Conversation Records</CardTitle>
            <div className="relative mt-3">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search message, intent or channel" value={query} onChange={(event) => setQuery(event.target.value)} />
            </div>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 space-y-2 overflow-auto">
            {filtered.length === 0 ? (
              <EmptyState title={loading ? "Loading conversations" : "No conversations found"} />
            ) : filtered.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={`w-full rounded-md border p-3 text-left text-sm transition ${selected?.id === item.id ? "border-primary bg-primary/5" : "bg-background hover:bg-muted/50"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-muted-foreground">#{item.id}</span>
                  <Badge>{item.intent || "unknown"}</Badge>
                </div>
                <p className="mt-2 line-clamp-2 font-medium">{item.user_message}</p>
                <p className="mt-1 text-xs text-muted-foreground">{item.channel} · {formatDateTime(item.created_at)}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="flex min-h-0 flex-col">
          <CardHeader>
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <CardTitle>{selected ? `Conversation #${selected.id}` : "Conversation Detail"}</CardTitle>
              {selected ? <Badge>{selected.channel}</Badge> : null}
            </div>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 overflow-auto">
            {!selected ? (
              <EmptyState title="Select a conversation" />
            ) : (
              <div className="space-y-4">
                <div className="rounded-md border bg-background p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                    <User className="h-4 w-4 text-primary" />
                    User Message
                  </div>
                  <p className="whitespace-pre-wrap text-sm">{selected.user_message}</p>
                </div>

                <div className="rounded-md border bg-background p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                    <Bot className="h-4 w-4 text-primary" />
                    Assistant Reply
                  </div>
                  <p className="whitespace-pre-wrap text-sm">{selected.assistant_reply}</p>
                </div>

                <div className="grid gap-4 xl:grid-cols-2">
                  <div className="rounded-md border bg-background p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                      <MessageSquareText className="h-4 w-4 text-primary" />
                      Structured Output
                    </div>
                    <pre className="max-h-80 overflow-auto rounded bg-muted p-3 text-xs">{JSON.stringify(selected.structured_output, null, 2)}</pre>
                  </div>

                  <div className="rounded-md border bg-background p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                      <CalendarClock className="h-4 w-4 text-primary" />
                      Runtime Events
                    </div>
                    {selectedEvents.length === 0 ? (
                      <EmptyState title="No events for this conversation" />
                    ) : (
                      <div className="space-y-2">
                        {selectedEvents.map((event) => (
                          <div key={event.id} className="rounded border bg-card p-2 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{event.type}</span>
                              <span className="text-muted-foreground">{formatDateTime(event.created_at)}</span>
                            </div>
                            <pre className="mt-2 max-h-32 overflow-auto rounded bg-muted p-2">{JSON.stringify(event.payload, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
