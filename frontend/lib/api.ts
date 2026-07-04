import type {
  AdminAnalytics,
  AdminError,
  Agent,
  ChatResponse,
  Conversation,
  Health,
  AdminToday,
  KnowledgeChunk,
  KnowledgeItem,
  Memory,
  Model,
  OllamaModel,
  OllamaStatus,
  PluginManifest,
  BrandProfile,
  BusinessTemplate,
  Prompt,
  RAGJob,
  Provider,
  Reservation,
  RuntimeEvent,
  Setting,
  VoiceCapabilities,
  WorkflowDefinition,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const HEALTH_URL = process.env.NEXT_PUBLIC_HEALTH_URL ?? "http://localhost:8000/health";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: async () => {
    const response = await fetch(HEALTH_URL, { cache: "no-store" });
    if (!response.ok) throw new Error("Backend health check failed");
    return response.json() as Promise<Health>;
  },
  analytics: () => request<AdminAnalytics>("/admin/analytics"),
  today: () => request<AdminToday>("/admin/today"),
  errors: () => request<AdminError[]>("/admin/errors"),
  conversations: () => request<Conversation[]>("/admin/conversations"),
  reservations: () => request<Reservation[]>("/reservations"),
  createReservation: (body: Partial<Reservation> & { customer_name: string; reservation_date: string; reservation_time: string; people: number }) =>
    request<Reservation>("/reservations", { method: "POST", body: JSON.stringify(body) }),
  updateReservation: (id: number, body: Partial<Reservation>) =>
    request<Reservation>(`/reservations/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  cancelReservation: (id: number) => request<Reservation>(`/reservations/${id}`, { method: "DELETE" }),
  chunks: () => request<KnowledgeChunk[]>("/knowledge/chunks"),
  searchKnowledge: (query: string) =>
    request<KnowledgeItem[]>("/knowledge/search", { method: "POST", body: JSON.stringify({ query, limit: 10 }) }),
  uploadKnowledge: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ source: string; documents: number; chunks: number }>("/knowledge/upload", { method: "POST", body: form });
  },
  agents: () => request<Agent[]>("/agents"),
  createAgent: (body: Partial<Agent> & { name: string }) => request<Agent>("/agents", { method: "POST", body: JSON.stringify(body) }),
  updateAgent: (id: number, body: Partial<Agent>) => request<Agent>(`/agents/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  providers: () => request<Provider[]>("/providers"),
  models: () => request<Model[]>("/models"),
  ollamaStatus: () => request<OllamaStatus>("/ollama/status"),
  ollamaModels: () => request<OllamaModel[]>("/ollama/models"),
  pullOllamaModel: async (model: string, onChunk: (chunk: string) => void) => {
    const response = await fetch(`${API_BASE_URL}/ollama/pull`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
    if (!response.ok || !response.body) {
      throw new Error(await response.text());
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
  },
  deleteOllamaModel: (name: string) =>
    request<{ deleted: boolean; model: string }>(`/ollama/models/${encodeURIComponent(name)}?confirm=true`, {
      method: "DELETE",
    }),
  settings: () => request<Setting[]>("/settings"),
  setProvider: (provider: string) => request<Setting>("/settings/provider", { method: "PUT", body: JSON.stringify({ provider }) }),
  setModel: (model: string) => request<Setting>("/settings/model", { method: "PUT", body: JSON.stringify({ model }) }),
  testModel: (message: string) =>
    request<{ provider: string; model: string; output: string }>("/settings/model/test", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  chat: (message: string, agent_id?: number) =>
    request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ message, agent_id, channel: "admin-playground" }) }),
  events: () => request<{ events: RuntimeEvent[] }>("/runtime/events"),
  memories: () => request<{ memories: Memory[] }>("/runtime/memories"),
  plugins: () => request<{ plugins: PluginManifest[] }>("/plugin-manifests"),
  prompts: () => request<Prompt[]>("/prompts"),
  createPrompt: (body: Partial<Prompt> & { name: string; content: string }) =>
    request<Prompt>("/prompts", { method: "POST", body: JSON.stringify(body) }),
  updatePrompt: (id: number, body: Partial<Prompt>) =>
    request<Prompt>(`/prompts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  templates: () => request<BusinessTemplate[]>("/business-templates"),
  applyTemplate: (slug: string) =>
    request<{ business_id: number; agent_id: number; prompts: number; knowledge_items: number }>(
      `/business-templates/${slug}/apply`,
      { method: "POST", body: JSON.stringify({}) },
    ),
  branding: () => request<BrandProfile>("/branding"),
  updateBranding: (body: Partial<BrandProfile>) =>
    request<BrandProfile>("/branding", { method: "PUT", body: JSON.stringify(body) }),
  ragJobs: () => request<RAGJob[]>("/rag/jobs"),
  workflows: () => request<WorkflowDefinition[]>("/workflows"),
  createWorkflow: (body: Partial<WorkflowDefinition> & { slug: string; name: string }) =>
    request<WorkflowDefinition>("/workflows", { method: "POST", body: JSON.stringify(body) }),
  voiceCapabilities: () => request<VoiceCapabilities>("/voice/capabilities"),
};
