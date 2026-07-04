"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { PluginManifest } from "@/types/api";

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<PluginManifest[]>([]);

  useEffect(() => {
    void api.plugins().then((value) => setPlugins(value.plugins));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Plugins</h1>
        <p className="text-sm text-muted-foreground">Registered plugin manifests and capability status.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Plugin Manifests</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {plugins.length === 0 ? <EmptyState title="No plugin manifests registered" detail="The backend is ready for manifests, but none have been installed yet." /> : plugins.map((plugin) => (
            <div key={plugin.id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{plugin.name}</p>
                <Badge>{plugin.version}</Badge>
                <Badge className={plugin.enabled ? "border-primary text-primary" : "border-destructive text-destructive"}>{plugin.enabled ? "enabled" : "disabled"}</Badge>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Capabilities</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {plugin.capabilities.length ? plugin.capabilities.map((capability) => <Badge key={capability}>{capability}</Badge>) : <span className="text-xs text-muted-foreground">No capabilities declared</span>}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
