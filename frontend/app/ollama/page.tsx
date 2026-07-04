"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Trash2 } from "lucide-react";

import { OllamaIcon } from "@/components/brand-icons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { OllamaModel, OllamaStatus, Setting } from "@/types/api";

function formatSize(size?: number | null) {
  if (!size) return "—";
  const gb = size / 1024 / 1024 / 1024;
  return `${gb.toFixed(gb >= 10 ? 0 : 1)} GB`;
}

export default function OllamaManagerPage() {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [pullModel, setPullModel] = useState("");
  const [pullLog, setPullLog] = useState("");
  const [message, setMessage] = useState("");

  const activeModel = settings.find((item) => item.key === "ai.model")?.value.name as string | undefined;

  async function load() {
    setMessage("");
    const [nextStatus, nextSettings] = await Promise.all([api.ollamaStatus(), api.settings()]);
    setStatus(nextStatus);
    setSettings(nextSettings);
    if (nextStatus.connected) {
      setModels(await api.ollamaModels());
    } else {
      setModels([]);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function selectModel(name: string) {
    await api.setProvider("ollama");
    await api.setModel(name);
    setMessage(`Active model set to ${name}.`);
    await load();
  }

  async function pull() {
    if (!pullModel) return;
    setPullLog("");
    await api.pullOllamaModel(pullModel, (chunk) => setPullLog((current) => `${current}${chunk}`));
    setPullModel("");
    await load();
  }

  async function deleteModel(name: string) {
    if (!window.confirm(`Delete Ollama model "${name}"?`)) return;
    await api.deleteOllamaModel(name);
    setMessage(`Deleted ${name}.`);
    await load();
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-md border bg-card">
          <OllamaIcon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Ollama Manager</h1>
          <p className="text-sm text-muted-foreground">Manage local or host Ollama without editing environment files.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Connection</CardTitle>
            <Button variant="outline" size="sm" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={status?.connected ? "border-primary text-primary" : "border-destructive text-destructive"}>
              {status?.connected ? "connected" : "disconnected"}
            </Badge>
            <span className="text-muted-foreground">{status?.url ?? "No reachable Ollama URL"}</span>
            {status?.version ? <Badge>v{status.version}</Badge> : null}
          </div>
          {message ? <p className="text-muted-foreground">{message}</p> : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader><CardTitle>Pull Model</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="llama3.1:8b" value={pullModel} onChange={(event) => setPullModel(event.target.value)} />
            <Button disabled={!pullModel || !status?.connected} onClick={() => void pull()}>Pull</Button>
            {pullLog ? <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">{pullLog}</pre> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Installed Models</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {models.length === 0 ? (
              <EmptyState title={status?.connected ? "No models installed" : "Ollama is not connected"} />
            ) : models.map((model) => (
              <div key={model.name} className="rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{model.name}</p>
                      {activeModel === model.name ? <Badge>active</Badge> : null}
                    </div>
                    <p className="text-muted-foreground">
                      {formatSize(model.size)} · {model.modified_at ?? "unknown modified date"}
                    </p>
                    {model.digest ? <p className="mt-1 break-all text-xs text-muted-foreground">{model.digest}</p> : null}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => void selectModel(model.name)}>Use</Button>
                    <Button variant="destructive" size="icon" title="Delete model" onClick={() => void deleteModel(model.name)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {model.details ? <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">{JSON.stringify(model.details, null, 2)}</pre> : null}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
