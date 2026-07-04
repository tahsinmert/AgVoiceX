"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Agent, Model, Provider } from "@/types/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [form, setForm] = useState({ name: "", provider: "ollama", model: "", system_prompt: "You are a helpful local business AI agent." });

  const load = () => void api.agents().then(setAgents);
  useEffect(() => {
    load();
    void api.providers().then(setProviders);
    void api.models().then(setModels).catch(() => setModels([]));
  }, []);

  async function createAgent() {
    await api.createAgent(form);
    setForm({ ...form, name: "" });
    load();
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Agents</h1>
        <p className="text-sm text-muted-foreground">Create and manage local business agents.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader><CardTitle>Create Agent</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Agent name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
              {providers.map((provider) => <option key={provider.name}>{provider.name}</option>)}
            </Select>
            <Select value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}>
              <option value="">Use selected/default model</option>
              {models.map((model) => <option key={model.name}>{model.name}</option>)}
            </Select>
            <Textarea value={form.system_prompt} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })} />
            <Button onClick={createAgent} disabled={!form.name}>Create</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Agent List</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {agents.length === 0 ? <EmptyState title="No agents yet" /> : agents.map((agent) => (
              <div key={agent.id} className="rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">{agent.name}</p>
                  <Badge>{agent.is_active ? "active" : "disabled"}</Badge>
                  <Badge>{agent.provider ?? "default provider"}</Badge>
                  <Badge>{agent.model || "default model"}</Badge>
                </div>
                <p className="mt-2 text-muted-foreground">{agent.system_prompt}</p>
                <div className="mt-3 flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => void api.updateAgent(agent.id, { is_active: !agent.is_active }).then(load)}>
                    {agent.is_active ? "Disable" : "Enable"}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
