"use client";

import { Headphones, Lock, Mic2, ServerCog, Waves } from "lucide-react";

import { VoiceClient } from "@/components/voice/voice-client";

export default function VoicePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-500">
            <Mic2 className="h-3.5 w-3.5" />
            Voice agent studio
          </div>
          <h1 className="text-3xl font-semibold">Build, test, and operate local voice agents.</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            A simple local alternative to hosted voice-agent platforms: speak, route intent, execute tools, and persist the result without usage limits.
          </p>
        </div>
      </div>

      <VoiceClient />

      <div className="grid gap-4 md:grid-cols-4">
        <Capability icon={Lock} title="Local first" text="Your provider, database, knowledge, and voice pipeline run under your control." />
        <Capability icon={ServerCog} title="Model routed" text="Ollama and LM Studio models are selected through the same runtime." />
        <Capability icon={Waves} title="Voice native" text="Speech turns become real conversation records and tool calls." />
        <Capability icon={Headphones} title="Operator ready" text="Use typed fallback whenever microphone, STT, or TTS setup needs attention." />
      </div>
    </div>
  );
}

function Capability({ icon: Icon, title, text }: { icon: typeof Lock; title: string; text: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-emerald-500">
        <Icon className="h-4 w-4" />
      </div>
      <h2 className="text-sm font-semibold">{title}</h2>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p>
    </div>
  );
}
