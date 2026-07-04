import { Inbox } from "lucide-react";

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="flex min-h-32 flex-col items-center justify-center rounded-lg border border-dashed bg-card p-6 text-center">
      <Inbox className="mb-2 h-5 w-5 text-muted-foreground" />
      <p className="text-sm font-medium">{title}</p>
      {detail ? <p className="mt-1 max-w-md text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}
