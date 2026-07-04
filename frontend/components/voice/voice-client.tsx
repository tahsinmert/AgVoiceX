"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  AudioLines,
  Bot,
  CheckCircle2,
  Loader2,
  Mic,
  MicOff,
  PhoneOff,
  Send,
  Sparkles,
  Volume2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { VoiceCapabilities } from "@/types/api";

type VoiceEvent = {
  type?: "ready" | "transcript" | "audio" | "error";
  text?: string;
  reply?: string;
  intent?: string;
  conversation_id?: number;
  message?: string;
};

type Turn = {
  id: string;
  user: string;
  agent: string;
  intent?: string;
};

export function VoiceClient({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState("Ready");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [typedMessage, setTypedMessage] = useState("");
  const [error, setError] = useState("");
  const [capabilities, setCapabilities] = useState<VoiceCapabilities | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);

  const wsUrl = useMemo(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001/api/v1";
    return `${base.replace(/^http/, "ws")}/voice/stream`;
  }, []);

  useEffect(() => {
    void api.voiceCapabilities().then(setCapabilities).catch(() => setCapabilities(null));
    return () => {
      cleanupRecorder();
      closeSocket();
    };
  }, []);

  async function ensureSocket() {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;

    setStatus("Connecting");
    setError("");

    const ws = new WebSocket(wsUrl);
    ws.binaryType = "blob";
    ws.onmessage = handleSocketMessage;
    ws.onerror = () => {
      setError("Voice socket connection failed. Check backend and refresh.");
      setStatus("Offline");
      setIsProcessing(false);
      setIsRecording(false);
    };
    ws.onclose = () => {
      wsRef.current = null;
      setStatus((current) => (current === "Processing" ? "Disconnected" : current));
      setIsProcessing(false);
      setIsRecording(false);
    };

    wsRef.current = ws;

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => {
        setStatus("Connected");
        resolve();
      };
      ws.onerror = () => reject(new Error("Voice socket connection failed."));
    });

    return ws;
  }

  async function startRecording() {
    try {
      const ws = await ensureSocket();
      if (ws.readyState !== WebSocket.OPEN) return;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        cleanupRecorder();
        if (blob.size === 0 || ws.readyState !== WebSocket.OPEN) {
          setStatus("Ready");
          return;
        }
        setIsProcessing(true);
        setStatus("Processing");
        ws.send(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setStatus("Listening");
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Microphone access failed.");
      setStatus("Ready");
      setIsRecording(false);
      setIsProcessing(false);
      cleanupRecorder();
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }

  async function sendTypedMessage() {
    const message = typedMessage.trim();
    if (!message) return;
    setTypedMessage("");
    setIsProcessing(true);
    setStatus("Processing");
    setError("");
    try {
      const response = await api.chat(message);
      setTurns((items) => [
        {
          id: String(response.conversation_id),
          user: message,
          agent: response.reply,
          intent: response.intent.intent,
        },
        ...items,
      ]);
      setStatus("Ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Message failed.");
      setStatus("Ready");
    } finally {
      setIsProcessing(false);
    }
  }

  async function handleSocketMessage(event: MessageEvent) {
    if (typeof event.data === "string") {
      const message = JSON.parse(event.data) as VoiceEvent;
      if (message.type === "ready") {
        setStatus("Connected");
        return;
      }
      if (message.type === "transcript") {
        setTurns((items) => [
          {
            id: String(message.conversation_id ?? Date.now()),
            user: message.text ?? "",
            agent: message.reply ?? "",
            intent: message.intent,
          },
          ...items,
        ]);
        setStatus("Reply ready");
        setIsProcessing(false);
        return;
      }
      if (message.type === "error") {
        setError(message.message ?? "Voice processing failed.");
        setStatus("Ready");
        setIsProcessing(false);
      }
      return;
    }

    if (event.data instanceof Blob) {
      await playAudio(event.data);
      setStatus("Ready");
      setIsProcessing(false);
    }
  }

  async function playAudio(blob: Blob) {
    try {
      if (!audioContextRef.current) audioContextRef.current = new AudioContext();
      const buffer = await blob.arrayBuffer();
      const audioBuffer = await audioContextRef.current.decodeAudioData(buffer);
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start(0);
    } catch {
      setError("Reply text is ready, but audio playback failed.");
    }
  }

  function cleanupRecorder() {
    mediaRecorderRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function closeSocket() {
    wsRef.current?.close();
    wsRef.current = null;
  }

  const stateLabel = isRecording ? "Listening" : isProcessing ? "Thinking" : status;

  return (
    <div className={compact ? "space-y-4" : "grid gap-5 lg:grid-cols-[minmax(320px,0.72fr)_minmax(0,1fr)]"}>
      <div className="rounded-lg border border-border bg-background p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold">Live Voice Agent</h2>
            <p className="mt-1 text-xs text-muted-foreground">Push-to-talk, local STT, local LLM, optional local TTS.</p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            {stateLabel}
          </span>
        </div>

        <div className="mb-4 grid gap-2 sm:grid-cols-2">
          <CapabilityPill active={capabilities?.stt_available} label="Local STT" detail={capabilities?.stt_model_path ?? "checking"} />
          <CapabilityPill active={capabilities?.tts_available} label="Local TTS" detail={capabilities?.tts_available ? capabilities.tts_model_name : "text replies still work"} />
        </div>

        <div className="flex flex-col items-center gap-5 py-4">
          <div className="relative flex h-44 w-44 items-center justify-center rounded-full border border-border bg-card">
            <div className={`absolute inset-3 rounded-full border ${isRecording ? "border-emerald-500/60" : "border-border"}`} />
            <div className={`absolute inset-8 rounded-full ${isRecording ? "bg-emerald-500/15" : "bg-muted/40"}`} />
            {isProcessing ? (
              <Loader2 className="relative h-14 w-14 animate-spin text-emerald-500" />
            ) : (
              <AudioLines className={`relative h-16 w-16 ${isRecording ? "text-emerald-500" : "text-muted-foreground"}`} />
            )}
          </div>

          <div className="flex items-center gap-3">
            {isRecording ? (
              <Button onClick={stopRecording} className="h-12 gap-2 bg-red-600 px-5 text-white hover:bg-red-700">
                <PhoneOff className="h-4 w-4" />
                Finish turn
              </Button>
            ) : (
              <Button onClick={startRecording} disabled={isProcessing} className="h-12 gap-2 px-5">
                <Mic className="h-4 w-4" />
                Talk now
              </Button>
            )}
            <Button variant="secondary" size="icon" disabled={!wsRef.current && !isRecording} onClick={closeSocket} title="Close voice socket">
              <MicOff className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <input
            value={typedMessage}
            onChange={(event) => setTypedMessage(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void sendTypedMessage();
            }}
            placeholder="Type a fallback request..."
            className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-primary"
          />
          <Button size="icon" onClick={() => void sendTypedMessage()} disabled={!typedMessage.trim() || isProcessing}>
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-300">
            {error}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-border bg-background">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-emerald-500" />
            <h2 className="text-sm font-semibold">Conversation</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Volume2 className="h-3.5 w-3.5" />
            Audio replies when TTS is configured
          </div>
        </div>
        <div className="max-h-[520px] space-y-4 overflow-auto p-5">
          {turns.length ? (
            turns.map((turn) => (
              <div key={turn.id} className="space-y-3">
                <div className="ml-auto max-w-[86%] rounded-lg bg-emerald-500 px-4 py-3 text-sm text-white">
                  {turn.user}
                </div>
                <div className="max-w-[86%] rounded-lg border border-border bg-card px-4 py-3 text-sm">
                  <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <Sparkles className="h-3.5 w-3.5 text-emerald-500" />
                    {turn.intent ?? "agent"}
                  </div>
                  {turn.agent}
                </div>
              </div>
            ))
          ) : (
            <div className="flex min-h-72 flex-col items-center justify-center text-center">
              <AudioLines className="mb-3 h-10 w-10 text-muted-foreground" />
              <p className="text-sm font-medium">No voice turns yet</p>
              <p className="mt-1 max-w-sm text-xs leading-5 text-muted-foreground">
                Try: “Book a table for two tomorrow at seven. My name is Ada and my phone is 555-0101.”
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CapabilityPill({ active, label, detail }: { active?: boolean; label: string; detail: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="flex items-center gap-2 text-xs font-medium">
        <span className={`h-2 w-2 rounded-full ${active ? "bg-emerald-500" : "bg-amber-500"}`} />
        {label}
      </div>
      <div className="mt-1 truncate text-[11px] text-muted-foreground">{detail}</div>
    </div>
  );
}
