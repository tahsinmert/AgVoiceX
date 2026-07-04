"use client";

import { useEffect, useMemo, useState } from "react";

import { OllamaIcon } from "@/components/brand-icons";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Model, Provider, Setting } from "@/types/api";

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [testMessage, setTestMessage] = useState("Return a short JSON health response.");
  const [testResult, setTestResult] = useState("");

  const selectedProvider = useMemo(() => settings.find((item) => item.key === "ai.provider")?.value.name as string | undefined, [settings]);
  const selectedModel = useMemo(() => settings.find((item) => item.key === "ai.model")?.value.name as string | undefined, [settings]);

  const load = () => {
    void api.providers().then(setProviders);
    void api.models().then(setModels).catch(() => setModels([]));
    void api.settings().then(setSettings);
  };
  useEffect(load, []);

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-md border bg-card">
            <OllamaIcon className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">Model Settings</h1>
            <p className="text-sm text-muted-foreground">Select providers and installed models.</p>
          </div>
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Provider and Model</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">Current provider: {selectedProvider ?? "default"}</p>
            <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="">Choose provider</option>
              {providers.map((item) => <option key={item.name}>{item.name}</option>)}
            </Select>
            <Button onClick={() => void api.setProvider(provider).then(load)} disabled={!provider}>Save Provider</Button>
            <p className="pt-3 text-sm text-muted-foreground">Current model: {selectedModel ?? "auto-selected from provider"}</p>
            <Select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="">Choose installed model</option>
              {models.map((item) => <option key={item.name}>{item.name}</option>)}
            </Select>
            <Button onClick={() => void api.setModel(model).then(load)} disabled={!model}>Save Model</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Test Model</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Textarea value={testMessage} onChange={(e) => setTestMessage(e.target.value)} />
            <Button onClick={() => void api.testModel(testMessage).then((value) => setTestResult(JSON.stringify(value, null, 2))).catch((error) => setTestResult(String(error)))}>Run Test</Button>
            {testResult ? <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{testResult}</pre> : <EmptyState title="No test response yet" />}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
