// Backend base URL is configured via Vite env var.
// In dev, set VITE_API_BASE=http://localhost:8000
// In production (e.g. Vercel), set VITE_API_BASE to your public backend URL or Cloudflare tunnel.
const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || (typeof import.meta !== "undefined" ? (import.meta as any).env?.VITE_API_BASE : undefined) || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }

  return (await res.json()) as T;
}

export interface Schema {
  id: number;
  name: string;
  description?: string | null;
  raw_schema: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: number;
  title?: string | null;
  schema_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface ChatResponse {
  sql: string;
  explanation?: string | null;
  raw_model_output: string;
}

export interface AuthUser {
  id: number;
  email: string;
}

export async function bootstrapUser(): Promise<{ user_id: number }> {
  return request<{ user_id: number }>("/api/users/bootstrap");
}

export async function signup(email: string, password: string): Promise<AuthUser> {
  return request<AuthUser>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<AuthUser> {
  return request<AuthUser>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<void> {
  await request<unknown>("/api/auth/logout", { method: "POST" });
}

export async function me(): Promise<AuthUser> {
  return request<AuthUser>("/api/auth/me");
}

export async function listSchemas(): Promise<Schema[]> {
  return request<Schema[]>("/api/schemas");
}

export async function createSchema(payload: {
  name: string;
  description?: string;
  raw_schema: string;
}): Promise<Schema> {
  return request<Schema>("/api/schemas", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listSessions(): Promise<Session[]> {
  return request<Session[]>("/api/sessions");
}

export async function createSession(payload: {
  title?: string;
  schema_id?: number | null;
}): Promise<Session> {
  return request<Session>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listMessages(sessionId: number): Promise<Message[]> {
  return request<Message[]>(`/api/sessions/${sessionId}/messages`);
}

export async function sendMessage(sessionId: number, content: string): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

