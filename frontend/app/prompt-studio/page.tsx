"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Plus, Search, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Prompt } from "@/types/api";

const DEFAULT_PROMPT = "You are a professional local voice reservation agent. Ask for missing booking details before creating a reservation.";

export default function PromptStudioPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [content, setContent] = useState(DEFAULT_PROMPT);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    void api.prompts().then((data) => {
      setPrompts(data);
      setSelectedId((current) => current ?? data[0]?.id ?? null);
    }).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return prompts;
    return prompts.filter((prompt) => [prompt.name, prompt.content, prompt.version, prompt.is_active ? "active" : "inactive"].join(" ").toLowerCase().includes(needle));
  }, [prompts, query]);

  const selected = prompts.find((prompt) => prompt.id === selectedId) ?? null;

  useEffect(() => {
    if (!selected) return;
    setName(selected.name);
    setContent(selected.content);
  }, [selected]);

  async function createPrompt() {
    const prompt = await api.createPrompt({ name: name || "Reservation Prompt", content, version: 1, is_active: false });
    setSelectedId(prompt.id);
    load();
  }

  async function savePrompt() {
    if (!selected) return;
    await api.updatePrompt(selected.id, { name, content });
    load();
  }

  async function activatePrompt(prompt: Prompt) {
    await api.updatePrompt(prompt.id, { is_active: !prompt.is_active });
    load();
  }

  return (
    <div className="flex h-[calc(100vh-6.5rem)] min-h-[620px] flex-col gap-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Prompt Studio</h1>
          <p className="text-sm text-muted-foreground">Create, edit and activate real prompts stored in the backend.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>Refresh</Button>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="flex min-h-0 flex-col">
          <CardHeader>
            <CardTitle>Prompt Records</CardTitle>
            <div className="relative mt-3">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search prompts" value={query} onChange={(event) => setQuery(event.target.value)} />
            </div>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 space-y-2 overflow-auto">
            {filtered.length === 0 ? (
              <EmptyState title={loading ? "Loading prompts" : "No prompts found"} />
            ) : filtered.map((prompt) => (
              <button
                key={prompt.id}
                type="button"
                onClick={() => setSelectedId(prompt.id)}
                className={`w-full rounded-md border p-3 text-left text-sm transition ${selectedId === prompt.id ? "border-primary bg-primary/5" : "bg-background hover:bg-muted/50"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{prompt.name}</p>
                  <Badge>{prompt.is_active ? "active" : "inactive"}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">v{prompt.version}</p>
                <p className="mt-2 line-clamp-2 text-muted-foreground">{prompt.content}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="flex min-h-0 flex-col">
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <CardTitle>{selected ? "Edit Prompt" : "New Prompt"}</CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => { setSelectedId(null); setName(""); setContent(DEFAULT_PROMPT); }}>
                  <Plus className="h-4 w-4" />
                  New
                </Button>
                {selected ? (
                  <Button variant="outline" onClick={() => void activatePrompt(selected)}>
                    <CheckCircle2 className="h-4 w-4" />
                    {selected.is_active ? "Deactivate" : "Activate"}
                  </Button>
                ) : null}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex min-h-0 flex-1 flex-col gap-3">
            <Input placeholder="Prompt name" value={name} onChange={(event) => setName(event.target.value)} />
            <Textarea className="min-h-0 flex-1 font-mono" value={content} onChange={(event) => setContent(event.target.value)} />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{content.length} characters</span>
              <span className="inline-flex items-center gap-1"><Sparkles className="h-3.5 w-3.5 text-primary" /> Saved in backend</span>
            </div>
            <Button onClick={() => void (selected ? savePrompt() : createPrompt())} disabled={!name.trim() || !content.trim()}>
              {selected ? "Save prompt" : "Create prompt"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
