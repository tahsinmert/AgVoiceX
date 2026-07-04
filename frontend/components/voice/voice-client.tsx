"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export function VoiceClient() {
  const [isCalling, setIsCalling] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [status, setStatus] = useState("Disconnected");
  const [lastTranscript, setLastTranscript] = useState("");
  const [lastReply, setLastReply] = useState("");
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    return () => stopCall();
  }, []);

  const startCall = async () => {
    try {
      setStatus("Connecting...");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const wsUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace("http", "ws") || "ws://localhost:8000/api/v1";
      const ws = new WebSocket(`${wsUrl}/voice/stream`);
      
      ws.onopen = () => {
        setStatus("Connected");
        setIsCalling(true);
        
        const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(e.data);
          }
        };
        
        mediaRecorder.start(250); // Send chunks every 250ms
        mediaRecorderRef.current = mediaRecorder;
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
          const message = JSON.parse(event.data) as { type?: string; text?: string; reply?: string; message?: string };
          if (message.type === "transcript") {
            setLastTranscript(message.text ?? "");
            setLastReply(message.reply ?? "");
            setStatus("Agent replied");
          } else if (message.type === "error") {
            setStatus(message.message ?? "Voice processing failed");
          }
          return;
        }

        if (event.data instanceof Blob) {
          if (!audioContextRef.current) {
            audioContextRef.current = new AudioContext();
          }
          const audioBuffer = await event.data.arrayBuffer();
          audioContextRef.current.decodeAudioData(audioBuffer, (buffer) => {
            const source = audioContextRef.current!.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContextRef.current!.destination);
            source.start(0);
          });
        }
      };

      ws.onclose = () => {
        setStatus("Disconnected");
        stopCall();
      };
      
      wsRef.current = ws;

    } catch (err) {
      console.error("Error accessing microphone:", err);
      setStatus("Error: Microphone access denied");
    }
  };

  const stopCall = () => {
    setIsCalling(false);
    
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      mediaRecorderRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setStatus("Disconnected");
  };

  const toggleMute = () => {
    if (mediaRecorderRef.current) {
      const audioTrack = mediaRecorderRef.current.stream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-card border rounded-lg shadow-sm space-y-6">
      <div className="relative flex items-center justify-center w-32 h-32 rounded-full bg-muted">
        {/* Dynamic visualizer can go here */}
        <div className={`absolute inset-0 rounded-full transition-all duration-300 ${isCalling ? 'bg-primary/20 animate-pulse' : ''}`} />
        <Mic className={`w-12 h-12 ${isCalling ? 'text-primary' : 'text-muted-foreground'}`} />
      </div>

      <div className="text-center">
        <h3 className="text-lg font-semibold">Voice Agent</h3>
        <p className="text-sm text-muted-foreground">{status}</p>
      </div>

      {(lastTranscript || lastReply) && (
        <div className="w-full max-w-xl space-y-2 rounded-md border border-border bg-muted/30 p-3 text-sm">
          {lastTranscript && <p><span className="font-medium">You:</span> {lastTranscript}</p>}
          {lastReply && <p><span className="font-medium">Agent:</span> {lastReply}</p>}
        </div>
      )}

      <div className="flex items-center gap-4">
        {isCalling ? (
          <>
            <Button 
              variant={isMuted ? "destructive" : "secondary"} 
              size="icon" 
              className="rounded-full w-12 h-12"
              onClick={toggleMute}
            >
              {isMuted ? <MicOff /> : <Mic />}
            </Button>
            <Button 
              variant="destructive" 
              size="icon" 
              className="rounded-full w-14 h-14"
              onClick={stopCall}
            >
              <PhoneOff />
            </Button>
          </>
        ) : (
          <Button 
            variant="default" 
            size="icon" 
            className="rounded-full w-14 h-14 bg-green-600 hover:bg-green-700 text-white"
            onClick={startCall}
          >
            <Phone />
          </Button>
        )}
      </div>
    </div>
  );
}
