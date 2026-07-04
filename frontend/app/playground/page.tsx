"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Agent, ChatResponse, Memory, RuntimeEvent } from "@/types/api";

export default function PlaygroundPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentId, setAgentId] = useState("");
  const [message, setMessage] = useState("Do you have baklava?");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void api.agents().then(setAgents);
    void api.events().then((value) => setEvents(value.events));
    void api.memories().then((value) => setMemories(value.memories));
  }, []);

  async function send() {
    setError("");
    try {
      const result = await api.chat(message, agentId ? Number(agentId) : undefined);
      setResponse(result);
      setEvents((await api.events()).events);
      setMemories((await api.memories()).memories);
    } catch (exc) {
      setError(String(exc));
    }
  }

  const relatedEvents = response ? events.filter((event) => event.conversation_id === response.conversation_id) : events.slice(0, 5);
  const toolResult = response ? response.intent : null;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Playground</h1>
        <p className="text-sm text-muted-foreground">Send a test message and inspect runtime output.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader><CardTitle>Test Message</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Select value={agentId} onChange={(e) => setAgentId(e.target.value)}>
              <option value="">Use active/default agent</option>
              {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}
            </Select>
            <Textarea value={message} onChange={(e) => setMessage(e.target.value)} />
            <Button onClick={send} disabled={!message}>Send</Button>
            {error ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs text-destructive">{error}</pre> : null}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Raw JSON</CardTitle></CardHeader>
            <CardContent>{response ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(response, null, 2)}</pre> : <EmptyState title="No response yet" />}</CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Tool Execution and Retrieval</CardTitle></CardHeader>
            <CardContent>{toolResult ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(toolResult, null, 2)}</pre> : <EmptyState title="No tool execution yet" />}</CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Runtime Events</CardTitle></CardHeader>
            <CardContent>{relatedEvents.length ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(relatedEvents, null, 2)}</pre> : <EmptyState title="No runtime events yet" />}</CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Memory</CardTitle></CardHeader>
            <CardContent>{memories.length ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(memories.slice(0, 8), null, 2)}</pre> : <EmptyState title="No memory yet" />}</CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
