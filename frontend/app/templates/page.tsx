"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { BusinessTemplate } from "@/types/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<BusinessTemplate[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => { void api.templates().then(setTemplates); }, []);

  async function apply(slug: string) {
    const result = await api.applyTemplate(slug);
    setMessage(`Created agent ${result.agent_id}, ${result.prompts} prompts and ${result.knowledge_items} knowledge items.`);
  }

  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-semibold">Business Templates</h1><p className="text-sm text-muted-foreground">Apply white-label starter packs for common business types.</p></div>
      {message ? <Card><CardContent className="p-4 text-sm">{message}</CardContent></Card> : null}
      <div className="grid gap-4 lg:grid-cols-3">
        {templates.length === 0 ? <EmptyState title="No templates available" /> : templates.map((template) => (
          <Card key={template.id}>
            <CardHeader><CardTitle>{template.name}</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Badge>{template.category}</Badge>
              <p className="text-muted-foreground">{template.description}</p>
              <p>{template.default_prompts.length} prompts · {template.sample_knowledge.length} knowledge samples</p>
              <Button onClick={() => void apply(template.slug)}>Apply Template</Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
