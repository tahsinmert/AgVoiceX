"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { KnowledgeChunk, KnowledgeItem } from "@/types/api";

export default function KnowledgePage() {
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeItem[]>([]);
  const [message, setMessage] = useState("");

  const load = () => void api.chunks().then(setChunks);
  useEffect(load, []);

  async function upload(file?: File) {
    if (!file) return;
    const result = await api.uploadKnowledge(file);
    setMessage(`Imported ${result.documents} documents and ${result.chunks} chunks from ${result.source}.`);
    load();
  }

  async function search() {
    setResults(await api.searchKnowledge(query));
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <p className="text-sm text-muted-foreground">Upload local documents, inspect chunks and test fallback search.</p>
      </div>
      <div className="grid gap-4 xl:grid-cols-[380px_1fr]">
        <Card>
          <CardHeader><CardTitle>Upload</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input type="file" accept=".txt,.md,.markdown,.json,.csv" onChange={(e) => void upload(e.target.files?.[0])} />
            {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
            <div className="flex gap-2">
              <Input placeholder="Search knowledge" value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button onClick={search} disabled={!query}>Search</Button>
            </div>
            <div className="space-y-2">
              {results.map((item) => <div key={item.id} className="rounded-md border p-3 text-sm"><p className="font-medium">{item.title}</p><p className="text-muted-foreground">{item.body}</p></div>)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Chunks</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {chunks.length === 0 ? <EmptyState title="No knowledge chunks yet" detail="Upload TXT, Markdown, JSON or CSV to populate local retrieval." /> : chunks.map((chunk) => (
              <div key={chunk.id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{chunk.source ?? "knowledge"} · chunk {chunk.chunk_index}</p>
                <p className="mt-1 line-clamp-3 text-muted-foreground">{chunk.body}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
