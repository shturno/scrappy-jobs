const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ------- Types -------

export type JobStatus = "new" | "sent" | "skipped" | "error";

export interface Job {
  id: number;
  title: string;
  company: string;
  url: string;
  email: string | null;
  language: string | null;
  status: JobStatus;
  created_at: string;
  sent_at: string | null;
}

export interface EmailStats {
  total_sent_today: number;
  total_sent_all: number;
  errors_today: number;
}

export interface AppConfig {
  search_keywords: string[];
  search_cities: string[];
  daily_limit: number;
  sender_name: string;
  sender_linkedin: string;
  sender_github: string;
  sender_portfolio: string;
}

export interface ConfigUpdate {
  search_keywords: string[];
  search_cities: string[];
}

export interface PipelineSummary {
  scraped: number;
  emails_found: number;
  sent: number;
  errors: number;
}

// ------- Helpers -------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ------- Endpoints -------

export function getStats(): Promise<EmailStats> {
  return apiFetch<EmailStats>("/api/emails/stats");
}

export function getJobs(params: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<Job[]> {
  const q = new URLSearchParams();
  if (params.status && params.status !== "all") q.set("status", params.status);
  if (params.limit != null) q.set("limit", String(params.limit));
  if (params.offset != null) q.set("offset", String(params.offset));
  return apiFetch<Job[]>(`/api/jobs?${q.toString()}`);
}

export function getConfig(): Promise<AppConfig> {
  return apiFetch<AppConfig>("/api/config");
}

export function runPipeline(): Promise<PipelineSummary> {
  return apiFetch<PipelineSummary>("/api/pipeline/run", { method: "POST" });
}

export function updateConfig(data: ConfigUpdate): Promise<AppConfig> {
  return apiFetch<AppConfig>("/api/config", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
