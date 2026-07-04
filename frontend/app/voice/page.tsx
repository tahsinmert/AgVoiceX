"use client";

import { VoiceClient } from "@/components/voice/voice-client";

export default function VoicePage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Real-time Streaming Voice Agent</h1>
        <p className="text-sm text-muted-foreground">
          Low-latency WebSocket streaming. Audio is sent and received in real-time.
        </p>
      </div>
      <VoiceClient />
    </div>
  );
}
