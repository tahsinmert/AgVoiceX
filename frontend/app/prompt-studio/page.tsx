"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Prompt } from "@/types/api";

export default function PromptStudioPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [form, setForm] = useState({ name: "", content: "", version: 1 });
  const load = () => void api.prompts().then(setPrompts);
  useEffect(load, []);
  async function create() {
    await api.createPrompt(form);
    setForm({ name: "", content: "", version: 1 });
    load();
  }
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Prompt Studio</h1><p className="text-sm text-muted-foreground">Create, version and activate prompts for local agents.</p></div>
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card><CardHeader><CardTitle>New Prompt Version</CardTitle></CardHeader><CardContent className="space-y-3">
          <Input placeholder="Prompt name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input type="number" min={1} value={form.version} onChange={(e) => setForm({ ...form, version: Number(e.target.value) })} />
          <Textarea className="min-h-52" placeholder="System instructions" value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
          <Button disabled={!form.name || !form.content} onClick={create}>Save Prompt</Button>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Prompt Versions</CardTitle></CardHeader><CardContent className="space-y-2">
          {prompts.length === 0 ? <EmptyState title="No prompts yet" /> : prompts.map((prompt) => (
            <div key={prompt.id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2"><p className="font-medium">{prompt.name}</p><Badge>v{prompt.version}</Badge><Badge>{prompt.is_active ? "active" : "inactive"}</Badge></div>
              <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{prompt.content}</p>
              <Button className="mt-3" variant="outline" size="sm" onClick={() => void api.updatePrompt(prompt.id, { is_active: !prompt.is_active }).then(load)}>{prompt.is_active ? "Deactivate" : "Activate"}</Button>
            </div>
          ))}
        </CardContent></Card>
      </div>
    </div>
  );
}
