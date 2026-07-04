"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, RefreshCw, Server, Settings, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Model, OllamaStatus, Provider, Setting } from "@/types/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("");
  const [testMessage, setTestMessage] = useState("Return a short JSON health response.");
  const [testResult, setTestResult] = useState("");
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);

  const load = () => {
    setLoading(true);
    void Promise.all([
      api.settings().then(setSettings),
      api.providers().then(setProviders),
      api.models().then(setModels).catch(() => setModels([])),
      api.ollamaStatus().then(setOllamaStatus).catch(() => setOllamaStatus(null)),
    ]).finally(() => setLoading(false));
  };

  useEffect(load, []);

  useEffect(() => {
    const providerSetting = settings.find((item) => item.key === "provider")?.value;
    const modelSetting = settings.find((item) => item.key === "model")?.value;
    const currentProvider = typeof providerSetting?.provider === "string" ? providerSetting.provider : "ollama";
    const currentModel = typeof modelSetting?.model === "string" ? modelSetting.model : "";
    setProvider(currentProvider);
    setModel(currentModel);
  }, [settings]);

  const providerModels = useMemo(() => models, [models]);

  async function saveProvider() {
    await api.setProvider(provider);
    load();
  }

  async function saveModel() {
    if (!model) return;
    await api.setModel(model);
    load();
  }

  async function runTest() {
    setTesting(true);
    setTestResult("");
    try {
      const result = await api.testModel(testMessage);
      setTestResult(JSON.stringify(result, null, 2));
    } catch (error) {
      setTestResult(error instanceof Error ? error.message : "Model test failed.");
    } finally {
      setTesting(false);
    }
  }

  const connected = Boolean(ollamaStatus?.connected);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Model Settings</h1>
          <p className="text-sm text-muted-foreground">Configure real providers, installed models and model health checks.</p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          Refresh
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <StatusCard label="Ollama" ok={connected} detail={ollamaStatus?.url || "Not connected"} />
        <StatusCard label="Installed models" ok={models.length > 0} detail={`${models.length} visible`} />
        <StatusCard label="Active provider" ok detail={provider} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader><CardTitle>Provider and Model</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium">Provider</label>
              <Select value={provider} onChange={(event) => setProvider(event.target.value)}>
                {providers.length === 0 ? <option value="ollama">ollama</option> : providers.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
              </Select>
              <Button onClick={saveProvider}>Save provider</Button>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Default model</label>
              <Select value={model} onChange={(event) => setModel(event.target.value)}>
                <option value="">Choose installed model</option>
                {providerModels.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
              </Select>
              <Button onClick={saveModel} disabled={!model}>Save model</Button>
            </div>

            <div className="rounded-md border bg-muted/40 p-3 text-sm">
              <p className="font-medium">Current settings</p>
              {settings.length === 0 ? (
                <p className="mt-1 text-muted-foreground">No settings stored yet.</p>
              ) : (
                <pre className="mt-2 overflow-auto rounded bg-background p-2 text-xs">{JSON.stringify(settings, null, 2)}</pre>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Test Model</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Textarea className="min-h-32" value={testMessage} onChange={(event) => setTestMessage(event.target.value)} />
            <Button onClick={runTest} disabled={!testMessage.trim() || testing}>
              {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Server className="h-4 w-4" />}
              Run test
            </Button>
            {testResult ? (
              <pre className="max-h-96 overflow-auto rounded-md bg-muted p-3 text-xs">{testResult}</pre>
            ) : (
              <EmptyState title="No test response yet" />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusCard({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div className={`rounded-lg border bg-card p-4 ${ok ? "" : "border-red-200 bg-red-50"}`}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{label}</p>
        <Badge className={ok ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}>
          {ok ? <CheckCircle2 className="mr-1 h-3 w-3" /> : <XCircle className="mr-1 h-3 w-3" />}
          {ok ? "OK" : "Issue"}
        </Badge>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}
