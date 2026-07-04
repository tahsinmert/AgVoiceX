"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  AudioLines,
  Bot,
  Building2,
  CalendarClock,
  Car,
  CheckCircle2,
  Dumbbell,
  Hotel,
  ListChecks,
  Loader2,
  Mic,
  MicOff,
  PhoneOff,
  Scissors,
  Send,
  Sparkles,
  Stethoscope,
  Utensils,
} from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type VoiceEvent = {
  type?: "ready" | "transcript" | "audio" | "error";
  text?: string;
  reply?: string;
  intent?: string;
  conversation_id?: number;
  reservation_id?: number | null;
  message?: string;
};

type Turn = {
  id: string;
  user: string;
  agent: string;
  intent?: string;
  reservationId?: number | null;
};

const reservationCategories = [
  {
    id: "hotel",
    label: "Hotel",
    icon: Hotel,
    scenario: "Hotel stay: capture guest name, phone, check-in date, arrival time, guests, room type, nights or checkout date, and special requests. Do not confirm without checkout date or nights.",
    example: "Book a deluxe room for two tomorrow at 18:00 for three nights. My name is Ada Lovelace.",
  },
  {
    id: "restaurant",
    label: "Dining",
    icon: Utensils,
    scenario: "Restaurant table: capture name, phone, date, time, party size, seating preference, allergies, and occasion.",
    example: "Reserve a table for four tomorrow at 20:00 under Ada Lovelace.",
  },
  {
    id: "clinic",
    label: "Clinic",
    icon: Stethoscope,
    scenario: "Clinic appointment: capture patient name, phone, preferred date and time, department or doctor, visit reason, and branch.",
    example: "I need a dental appointment tomorrow at 10 for Ada Lovelace.",
  },
  {
    id: "beauty",
    label: "Salon",
    icon: Scissors,
    scenario: "Beauty appointment: capture client name, phone, service, stylist preference, date, time, duration, and notes.",
    example: "Book a haircut for tomorrow at 15:00. My name is Ada.",
  },
  {
    id: "wellness",
    label: "Wellness",
    icon: Dumbbell,
    scenario: "Wellness or spa appointment: capture guest name, phone, treatment, therapist preference, date, time, duration, and health notes.",
    example: "Book a massage for two people tomorrow at 17:00.",
  },
  {
    id: "automotive",
    label: "Service",
    icon: Car,
    scenario: "Automotive service: capture customer name, phone, vehicle, requested service, date, time, location, and issue notes.",
    example: "Schedule car maintenance tomorrow morning for Ada, phone 555-0101.",
  },
  {
    id: "meeting_room",
    label: "Room",
    icon: Building2,
    scenario: "Meeting room booking: capture organizer name, phone or email, date, start time, attendee count, duration, room layout, and equipment.",
    example: "Reserve a meeting room for six tomorrow at 13:00 for two hours.",
  },
  {
    id: "generic",
    label: "General",
    icon: CalendarClock,
    scenario: "General reservation: identify the business context, then capture name, phone, date, time, people, service, and notes.",
    example: "I want to make a reservation for tomorrow afternoon.",
  },
];

export function VoiceClient({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState("Ready");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [typedMessage, setTypedMessage] = useState("");
  const [error, setError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("hotel");

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);

  const wsUrl = useMemo(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001/api/v1";
    const category = reservationCategories.find((item) => item.id === selectedCategory) ?? reservationCategories[0];
    const params = new URLSearchParams({
      reservation_type: category.id,
      scenario: category.scenario,
    });
    return `${base.replace(/^http/, "ws")}/voice/stream?${params.toString()}`;
  }, [selectedCategory]);

  const activeCategory = useMemo(
    () => reservationCategories.find((item) => item.id === selectedCategory) ?? reservationCategories[0],
    [selectedCategory],
  );

  useEffect(() => {
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
      const response = await api.chat(message, undefined, {
        reservation_type: activeCategory.id,
        scenario: activeCategory.scenario,
      });
      setTurns((items) => [
        {
          id: String(response.conversation_id),
          user: message,
          agent: response.reply,
          intent: response.intent.reservation_type || response.intent.intent,
          reservationId: response.reservation_id,
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
            reservationId: message.reservation_id,
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
    <div className="flex h-[calc(100vh-6.5rem)] min-h-[560px] flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Live Voice</h1>
          <p className="mt-1 text-sm text-muted-foreground">{activeCategory.label} reservation desk</p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
          {stateLabel}
        </span>
      </div>

      <div className={compact ? "space-y-4" : "grid min-h-0 flex-1 gap-4 lg:grid-cols-[360px_minmax(0,1fr)]"}>
        <div className="flex min-h-0 flex-col rounded-lg border border-border bg-background p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Call Control</h2>
            <span className="text-xs text-muted-foreground">{isRecording ? "Recording" : isProcessing ? "Processing" : "Idle"}</span>
          </div>

          <div className="mb-4 grid grid-cols-4 gap-2">
            {reservationCategories.map((category) => {
              const Icon = category.icon;
              const selected = category.id === selectedCategory;
              return (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => {
                    if (!isRecording && !isProcessing) {
                      closeSocket();
                      setSelectedCategory(category.id);
                    }
                  }}
                  disabled={isRecording || isProcessing}
                  className={`flex h-14 flex-col items-center justify-center gap-1 rounded-md border text-[11px] font-medium transition ${
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground"
                  }`}
                  title={category.scenario}
                >
                  <Icon className="h-4 w-4" />
                  <span>{category.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex flex-1 flex-col items-center justify-center gap-5 py-4">
            <div className="relative flex h-36 w-36 items-center justify-center rounded-full border border-border bg-card">
              <div className={`absolute inset-3 rounded-full border ${isRecording ? "border-primary/60" : "border-border"}`} />
              <div className={`absolute inset-8 rounded-full ${isRecording ? "bg-primary/10" : "bg-muted/40"}`} />
              {isProcessing ? (
                <Loader2 className="relative h-12 w-12 animate-spin text-primary" />
              ) : (
                <AudioLines className={`relative h-14 w-14 ${isRecording ? "text-primary" : "text-muted-foreground"}`} />
              )}
            </div>

            <div className="flex items-center gap-3">
              {isRecording ? (
                <Button onClick={stopRecording} className="h-11 gap-2 bg-red-600 px-5 text-white hover:bg-red-700">
                  <PhoneOff className="h-4 w-4" />
                  Stop
                </Button>
              ) : (
                <Button onClick={startRecording} disabled={isProcessing} className="h-11 gap-2 px-5">
                  <Mic className="h-4 w-4" />
                  Speak
                </Button>
              )}
              <Button variant="secondary" size="icon" disabled={!wsRef.current && !isRecording} onClick={closeSocket} title="Close connection">
                <MicOff className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="mt-auto flex gap-2">
            <input
              value={typedMessage}
              onChange={(event) => setTypedMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void sendTypedMessage();
              }}
              placeholder={activeCategory.example}
              className="h-10 min-w-0 flex-1 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-primary"
            />
            <Button size="icon" onClick={() => void sendTypedMessage()} disabled={!typedMessage.trim() || isProcessing}>
              <Send className="h-4 w-4" />
            </Button>
          </div>

          {error && (
            <div className="mt-3 rounded-md border border-red-500/20 bg-red-50 p-3 text-xs text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="flex min-h-0 flex-col rounded-lg border border-border bg-background">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold">Conversation</h2>
            </div>
          </div>
          <div className="min-h-0 flex-1 space-y-4 overflow-auto p-5">
            {turns.length ? (
              turns.map((turn) => (
                <div key={turn.id} className="space-y-3">
                  <div className="ml-auto max-w-[78%] rounded-lg bg-primary px-4 py-3 text-sm text-primary-foreground">
                    {turn.user}
                  </div>
                  <div className="max-w-[78%] rounded-lg border border-border bg-card px-4 py-3 text-sm">
                    <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <Sparkles className="h-3.5 w-3.5 text-primary" />
                      {turn.intent ?? "assistant"}
                    </div>
                    {turn.agent}
                    {turn.reservationId ? (
                      <div className="mt-3 flex flex-wrap items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Saved as reservation #{turn.reservationId}</span>
                        <Button asChild size="sm" variant="outline" className="ml-auto h-7 border-emerald-200 bg-white text-emerald-700 hover:bg-emerald-100">
                          <Link href="/reservations">
                            <ListChecks className="h-3.5 w-3.5" />
                            Open records
                          </Link>
                        </Button>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))
            ) : (
              <div className="flex h-full min-h-72 flex-col items-center justify-center text-center">
                <AudioLines className="mb-3 h-10 w-10 text-muted-foreground" />
                <p className="text-sm font-medium">No conversation yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
