"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, CheckCircle2, Plus, Search, ToggleLeft, ToggleRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Agent, Model, Provider } from "@/types/api";

const DEFAULT_PROMPT = [
  "You are a professional local voice reservation agent.",
  "Collect required details, ask concise follow-up questions, and create reservations only when the request is complete.",
  "Never invent customer details, dates, times, phone numbers, or booking details.",
].join("\n");

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    name: "",
    provider: "ollama",
    model: "",
    system_prompt: DEFAULT_PROMPT,
  });

  const load = () => {
    setLoading(true);
    void api.agents().then(setAgents).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    void api.providers().then(setProviders);
    void api.models().then(setModels).catch(() => setModels([]));
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return agents;
    return agents.filter((agent) => [agent.name, agent.provider, agent.model, agent.system_prompt].join(" ").toLowerCase().includes(needle));
  }, [agents, query]);

  const activeCount = agents.filter((agent) => agent.is_active).length;

  async function createAgent() {
    await api.createAgent({
      name: form.name,
      provider: form.provider,
      model: form.model || undefined,
      system_prompt: form.system_prompt,
      is_active: true,
    });
    setForm({ ...form, name: "" });
    load();
  }

  async function toggleAgent(agent: Agent) {
    await api.updateAgent(agent.id, { is_active: !agent.is_active });
    load();
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agents</h1>
          <p className="text-sm text-muted-foreground">Create and manage real backend agents used by live voice flows.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>Refresh</Button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Total agents" value={agents.length} />
        <Metric label="Active agents" value={activeCount} />
        <Metric label="Available models" value={models.length} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
        <Card>
          <CardHeader><CardTitle>New Agent</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Agent name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            <Select value={form.provider} onChange={(event) => setForm({ ...form, provider: event.target.value })}>
              {providers.length === 0 ? <option value="ollama">ollama</option> : providers.map((provider) => <option key={provider.name} value={provider.name}>{provider.name}</option>)}
            </Select>
            <Select value={form.model} onChange={(event) => setForm({ ...form, model: event.target.value })}>
              <option value="">Use default model</option>
              {models.map((model) => <option key={model.name} value={model.name}>{model.name}</option>)}
            </Select>
            <Textarea className="min-h-40" value={form.system_prompt} onChange={(event) => setForm({ ...form, system_prompt: event.target.value })} />
            <Button className="w-full" onClick={createAgent} disabled={!form.name.trim()}>
              <Plus className="h-4 w-4" />
              Create agent
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <CardTitle>Agent Records</CardTitle>
              <div className="relative w-full md:w-80">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input className="pl-9" placeholder="Search agents" value={query} onChange={(event) => setQuery(event.target.value)} />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {filtered.length === 0 ? (
              <EmptyState title={loading ? "Loading agents" : "No agents found"} />
            ) : filtered.map((agent) => (
              <div key={agent.id} className="grid gap-3 rounded-md border bg-background p-3 text-sm lg:grid-cols-[minmax(0,1fr)_auto]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Bot className="h-4 w-4 text-primary" />
                    <p className="font-medium">{agent.name}</p>
                    <Badge className={agent.is_active ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"}>
                      {agent.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <p className="mt-1 text-muted-foreground">{agent.provider || "default provider"} · {agent.model || "default model"}</p>
                  <p className="mt-2 line-clamp-2 text-muted-foreground">{agent.system_prompt}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void toggleAgent(agent)}>
                  {agent.is_active ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                  {agent.is_active ? "Disable" : "Enable"}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
        <CheckCircle2 className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
      </div>
    </div>
  );
}
