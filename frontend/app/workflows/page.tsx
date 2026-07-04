"use client";

import { useEffect, useState } from "react";
import { N8n } from "@thesvg/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { WorkflowDefinition } from "@/types/api";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [form, setForm] = useState({ slug: "", name: "", description: "", definition: "{\n  \"nodes\": []\n}" });
  const load = () => void api.workflows().then(setWorkflows);
  useEffect(load, []);
  async function create() {
    await api.createWorkflow({ ...form, definition: JSON.parse(form.definition) as Record<string, unknown> });
    setForm({ slug: "", name: "", description: "", definition: "{\n  \"nodes\": []\n}" });
    load();
  }
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-md border bg-card">
          <N8n className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Workflow Builder</h1>
          <p className="text-sm text-muted-foreground">Define workflow JSON for backend tools and n8n flows.</p>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card><CardHeader><CardTitle>Create Workflow</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input placeholder="slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Textarea className="min-h-48 font-mono" value={form.definition} onChange={(e) => setForm({ ...form, definition: e.target.value })} />
          <Button disabled={!form.slug || !form.name} onClick={create}>Save Workflow</Button>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Definitions</CardTitle></CardHeader><CardContent className="space-y-2">
          {workflows.length === 0 ? <EmptyState title="No workflows yet" /> : workflows.map((workflow) => (
            <div key={workflow.id} className="rounded-md border p-3 text-sm"><div className="flex gap-2"><p className="font-medium">{workflow.name}</p><Badge>{workflow.enabled ? "enabled" : "disabled"}</Badge></div><p className="text-muted-foreground">{workflow.description}</p><pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">{JSON.stringify(workflow.definition, null, 2)}</pre></div>
          ))}
        </CardContent></Card>
      </div>
    </div>
  );
}
