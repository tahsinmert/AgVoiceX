export type Health = {
  status?: string;
  api?: string;
  postgres?: string | boolean;
  redis?: string | boolean;
  qdrant?: string | boolean;
  ollama?: string | boolean;
  [key: string]: unknown;
};

export type AdminAnalytics = { reservations: number; customers: number; covers: number };
export type AdminToday = { date: string; reservations: number; covers: number };
export type AdminError = { id: number; source: string; message: string; details: Record<string, unknown>; created_at: string };

export type IntentPayload = {
  intent: string;
  reservation_type?: string;
  customer_name?: string;
  phone?: string;
  email?: string;
  date?: string;
  time?: string;
  people?: number | null;
  reservation_id?: number | null;
  service?: string;
  room_type?: string;
  checkout_date?: string;
  nights?: number | null;
  duration_minutes?: number | null;
  location?: string;
  notes?: string;
  question?: string;
  reply?: string;
};

export type Conversation = {
  id: number;
  organization_id?: number | null;
  customer_id?: number | null;
  channel: string;
  user_message: string;
  intent?: string | null;
  structured_output: Record<string, unknown>;
  assistant_reply: string;
  created_at: string;
};

export type RuntimeEvent = {
  id: number;
  type: string;
  conversation_id?: number | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type Memory = {
  id: number;
  customer_id?: number | null;
  type: string;
  content: string;
  metadata: Record<string, unknown>;
  updated_at: string;
};

export type Reservation = {
  id: number;
  organization_id?: number | null;
  business_id?: number | null;
  customer_id?: number | null;
  customer_name?: string;
  phone?: string | null;
  email?: string | null;
  reservation_date: string;
  reservation_time: string;
  people: number;
  status: string;
  notes?: string | null;
};

export type KnowledgeChunk = {
  id: number;
  organization_id: number;
  knowledge_id?: number | null;
  chunk_index: number;
  body: string;
  source?: string | null;
  metadata: Record<string, unknown>;
};

export type KnowledgeItem = {
  id: number;
  title: string;
  body: string;
  source?: string | null;
  metadata: Record<string, unknown>;
};

export type Agent = {
  id: number;
  organization_id?: number | null;
  business_id?: number | null;
  name: string;
  provider?: string | null;
  model: string;
  system_prompt: string;
  is_active: boolean;
};

export type Provider = { name: string };
export type Model = { name: string };

export type OllamaStatus = {
  connected: boolean;
  version?: string | null;
  url?: string | null;
};

export type OllamaModel = {
  name: string;
  size?: number | null;
  modified_at?: string | null;
  digest?: string | null;
  details?: Record<string, unknown> | null;
};

export type Setting = {
  id: number;
  key: string;
  value: Record<string, unknown>;
};

export type ChatResponse = {
  reply: string;
  intent: IntentPayload;
  conversation_id: number;
  customer_id?: number | null;
  reservation_id?: number | null;
};

export type PluginManifest = {
  id: number;
  organization_id?: number | null;
  name: string;
  version: string;
  enabled: boolean;
  capabilities: string[];
  config_schema: Record<string, unknown>;
};

export type Prompt = {
  id: number;
  organization_id: number;
  agent_id?: number | null;
  name: string;
  content: string;
  version: number;
  is_active: boolean;
};

export type BusinessTemplate = {
  id: number;
  slug: string;
  name: string;
  description: string;
  category: string;
  default_settings: Record<string, unknown>;
  default_prompts: Record<string, unknown>[];
  sample_knowledge: Record<string, unknown>[];
};

export type BrandProfile = {
  id: number;
  organization_id?: number | null;
  business_id?: number | null;
  name: string;
  logo_url?: string | null;
  primary_color: string;
  accent_color: string;
  support_email?: string | null;
  custom_domain?: string | null;
};

export type RAGJob = {
  id: number;
  organization_id: number;
  business_id?: number | null;
  source: string;
  status: string;
  documents: number;
  chunks: number;
  error?: string | null;
};

export type WorkflowDefinition = {
  id: number;
  organization_id: number;
  business_id?: number | null;
  slug: string;
  name: string;
  description: string;
  enabled: boolean;
  definition: Record<string, unknown>;
};

export type VoiceCapabilities = {
  stt_available: boolean;
  tts_available: boolean;
  stt_model_path: string;
  tts_model_name: string;
  tts_device: string;
  tts_language: string;
  mode: string;
};
