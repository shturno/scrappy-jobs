const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ------- Types -------

export type JobStatus = "new" | "applied" | "skipped" | "error";

export interface Job {
  id: number;
  title: string;
  company: string;
  url: string;
  location: string | null;
  language: string | null;
  status: JobStatus;
  dismissed: boolean;
  created_at: string;
}

export interface JobStats {
  total_jobs: number;
  new_today: number;
  errors_today: number;
  companies_tracked: number;
}

export interface ScrapeResult {
  id: number;
  title: string;
  company: string;
  url: string;
  location: string | null;
  language: string | null;
  status: string;
}

// ------- Helpers -------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY ?? "",
    },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ------- Endpoints -------

export function getStats(): Promise<JobStats> {
  return apiFetch<JobStats>("/api/jobs/stats");
}

export function getJobs(params: {
  status?: string;
  company?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<Job[]> {
  const q = new URLSearchParams();
  if (params.status && params.status !== "all") q.set("status", params.status);
  if (params.company && params.company !== "all") q.set("company", params.company);
  if (params.search) q.set("search", params.search);
  if (params.limit != null) q.set("limit", String(params.limit));
  if (params.skip != null) q.set("skip", String(params.skip));
  return apiFetch<Job[]>(`/api/jobs?${q.toString()}`);
}

export function scrapePipeline(): Promise<ScrapeResult[]> {
  return apiFetch<ScrapeResult[]>("/api/pipeline/scrape", { method: "POST" });
}

export function dismissJob(id: number): Promise<Job> {
  return apiFetch<Job>(`/api/jobs/${id}/dismiss`, { method: "PATCH" });
}

export function markApplied(id: number): Promise<Job> {
  return apiFetch<Job>(`/api/jobs/${id}/apply`, { method: "PATCH" });
}
