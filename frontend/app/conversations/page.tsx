"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { Conversation, RuntimeEvent } from "@/types/api";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);

  useEffect(() => {
    void api.conversations().then((value) => {
      setConversations(value);
      setSelected(value[0] ?? null);
    });
    void api.events().then((value) => setEvents(value.events));
  }, []);

  const selectedEvents = selected ? events.filter((event) => event.conversation_id === selected.id) : events.slice(0, 10);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Conversations</h1>
        <p className="text-sm text-muted-foreground">Inspect messages, intents, tool plans and runtime events.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader><CardTitle>Conversation List</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {conversations.length === 0 ? <EmptyState title="No conversations yet" /> : conversations.map((item) => (
              <button key={item.id} onClick={() => setSelected(item)} className="w-full rounded-md border p-3 text-left text-sm hover:bg-muted">
                <div className="flex items-center justify-between">
                  <span className="font-medium">#{item.id}</span>
                  <Badge>{item.intent ?? "unknown"}</Badge>
                </div>
                <p className="mt-1 truncate text-muted-foreground">{item.user_message}</p>
                <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(item.created_at)}</p>
              </button>
            ))}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Message Detail</CardTitle></CardHeader>
            <CardContent>
              {selected ? (
                <div className="space-y-3 text-sm">
                  <p><span className="font-medium">User:</span> {selected.user_message}</p>
                  <p><span className="font-medium">Assistant:</span> {selected.assistant_reply}</p>
                  <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(selected.structured_output, null, 2)}</pre>
                </div>
              ) : <EmptyState title="Select a conversation" />}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Runtime Events</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {selectedEvents.length === 0 ? <EmptyState title="No runtime events recorded" /> : selectedEvents.map((event) => (
                <div key={event.id} className="rounded-md border p-3 text-sm">
                  <div className="flex items-center justify-between"><Badge>{event.type}</Badge><span className="text-xs text-muted-foreground">{formatDateTime(event.created_at)}</span></div>
                  <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">{JSON.stringify(event.payload, null, 2)}</pre>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
