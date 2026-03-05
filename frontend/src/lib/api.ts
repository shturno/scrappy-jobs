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
  dismissed: boolean;
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

export interface ScrapeResult {
  id: number;
  title: string;
  company: string;
  url: string;
  email: string | null;
  language: string | null;
  status: string;
}

export interface EmailPreview {
  subject: string;
  body: string;
}

export interface SendSummary {
  sent: number;
  skipped: number;
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
  skip?: number;
  limit?: number;
}): Promise<Job[]> {
  const q = new URLSearchParams();
  if (params.status && params.status !== "all") q.set("status", params.status);
  if (params.limit != null) q.set("limit", String(params.limit));
  if (params.skip != null) q.set("skip", String(params.skip));
  return apiFetch<Job[]>(`/api/jobs?${q.toString()}`);
}

export function getConfig(): Promise<AppConfig> {
  return apiFetch<AppConfig>("/api/config");
}

export function runPipeline(): Promise<PipelineSummary> {
  return apiFetch<PipelineSummary>("/api/pipeline/run", { method: "POST" });
}

export function scrapePipeline(): Promise<ScrapeResult[]> {
  return apiFetch<ScrapeResult[]>("/api/pipeline/scrape", { method: "POST" });
}

export function getEmailPreview(jobId: number): Promise<EmailPreview> {
  return apiFetch<EmailPreview>(`/api/jobs/${jobId}/preview`);
}

export function sendSelectedJobs(jobIds: number[]): Promise<SendSummary> {
  return apiFetch<SendSummary>("/api/pipeline/send", {
    method: "POST",
    body: JSON.stringify({ job_ids: jobIds }),
  });
}

export function dismissJob(id: number): Promise<Job> {
  return apiFetch<Job>(`/api/jobs/${id}/dismiss`, { method: "PATCH" });
}

export function updateConfig(data: ConfigUpdate): Promise<AppConfig> {
  return apiFetch<AppConfig>("/api/config", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
