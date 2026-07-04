"use client";

import { useEffect, useState } from "react";
import { PostgresqlIcon, QdrantIcon } from "@/components/brand-icons";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { RAGJob } from "@/types/api";

export default function RAGPage() {
  const [jobs, setJobs] = useState<RAGJob[]>([]);
  useEffect(() => { void api.ragJobs().then(setJobs); }, []);
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-md border bg-card">
          <QdrantIcon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">RAG Ingestion Pipeline</h1>
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <PostgresqlIcon className="h-4 w-4" />
            PostgreSQL chunks with Qdrant indexing support.
          </p>
        </div>
      </div>
      <Card><CardHeader><CardTitle>Ingestion Jobs</CardTitle></CardHeader><CardContent className="space-y-2">
        {jobs.length === 0 ? <EmptyState title="No ingestion jobs yet" detail="Upload documents in Knowledge Base to create RAG jobs." /> : jobs.map((job) => (
          <div key={job.id} className="rounded-md border p-3 text-sm">
            <div className="flex items-center gap-2"><p className="font-medium">{job.source}</p><Badge>{job.status}</Badge></div>
            <p className="text-muted-foreground">{job.documents} documents · {job.chunks} chunks</p>
            {job.error ? <p className="text-destructive">{job.error}</p> : null}
          </div>
        ))}
      </CardContent></Card>
    </div>
  );
}
