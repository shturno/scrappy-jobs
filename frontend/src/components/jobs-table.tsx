"use client";

import { useEffect, useState } from "react";
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Satellite } from "lucide-react";
import { getJobs, type Job } from "@/lib/api";

const PAGE_SIZE = 20;

const STATUS_DOT: Record<string, string> = {
  sent:            "#10b981",
  email_collected: "#7c3aed",
  error:           "#f43f5e",
  new:             "rgba(255,255,255,0.3)",
  skipped:         "rgba(255,255,255,0.15)",
};

const STATUS_LABEL: Record<string, string> = {
  sent:            "text-emerald-400",
  email_collected: "text-violet-400",
  error:           "text-rose-400",
  new:             "text-white/40",
  skipped:         "text-white/25",
};

const LANG_CONFIG: Record<string, { color: string; bg: string }> = {
  pt: { color: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
  en: { color: "#38bdf8", bg: "rgba(56,189,248,0.12)" },
};

function timeAgo(iso: string): string {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function JobsTable() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [status, setStatus] = useState("all");
  const [lang, setLang] = useState("all");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);

  const filtered = lang === "all" ? jobs : jobs.filter((j) => j.language === lang);

  useEffect(() => {
    setLoading(true);
    getJobs({ status, limit: PAGE_SIZE, offset: page * PAGE_SIZE })
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, [status, page]);

  function changeLang(v: string) { setLang(v); setPage(0); }

  function renderRows() {
    if (loading) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="py-20 text-center">
            <div className="flex flex-col items-center gap-3">
              <div
                className="w-8 h-8 rounded-full border-2 border-t-violet-500 border-violet-500/20 animate-spin"
              />
              <span className="text-sm text-white/40">Scanning orbit…</span>
            </div>
          </TableCell>
        </TableRow>
      );
    }

    if (jobs.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="py-24 text-center">
            <div className="flex flex-col items-center gap-5">
              <div
                className="w-16 h-16 rounded-full border flex items-center justify-center"
                style={{ borderColor: "rgba(124,58,237,0.25)", background: "rgba(124,58,237,0.05)" }}
              >
                <Satellite size={26} className="text-violet-500/50" />
              </div>
              <div>
                <p className="text-base font-semibold text-white/30">No signals detected</p>
                <p className="text-sm mt-1 text-white/20">Launch the pipeline to start tracking</p>
              </div>
            </div>
          </TableCell>
        </TableRow>
      );
    }

    return filtered.map((job) => (
      <TableRow
        key={job.id}
        className="group cursor-pointer transition-colors duration-100"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
        onClick={() => window.open(job.url, "_blank")}
        onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "rgba(124,58,237,0.04)"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}
      >
        <TableCell className="py-4 pl-6">
          <span className="font-semibold text-white text-[13px]">{job.company}</span>
        </TableCell>
        <TableCell className="py-4 max-w-[220px]">
          <span className="text-[13px] truncate block" style={{ color: "rgba(255,255,255,0.5)" }}>
            {job.title}
          </span>
        </TableCell>
        <TableCell className="py-4">
          {job.language && (() => {
            const cfg = LANG_CONFIG[job.language];
            return cfg ? (
              <span
                className="text-[10px] font-bold uppercase px-2 py-1 rounded-md"
                style={{ color: cfg.color, background: cfg.bg }}
              >
                {job.language}
              </span>
            ) : null;
          })()}
        </TableCell>
        <TableCell className="py-4 max-w-[180px]">
          <span className="text-[12px] truncate block" style={{ color: "rgba(255,255,255,0.3)" }}>
            {job.email ?? "—"}
          </span>
        </TableCell>
        <TableCell className="py-4">
          <span className="flex items-center gap-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ background: STATUS_DOT[job.status] ?? "rgba(255,255,255,0.2)" }}
            />
            <span className={`text-[11px] font-medium capitalize ${STATUS_LABEL[job.status] ?? "text-white/30"}`}>
              {job.status}
            </span>
          </span>
        </TableCell>
        <TableCell className="py-4 pr-6 text-[11px] tabular-nums" style={{ color: "rgba(255,255,255,0.25)" }}>
          {timeAgo(job.created_at)}
        </TableCell>
      </TableRow>
    ));
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Select value={status} onValueChange={(v) => { setStatus(v); setPage(0); }}>
            <SelectTrigger
              className="w-[160px] h-8 text-xs font-medium rounded-lg"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.6)",
              }}
            >
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent
              style={{ background: "#0a0a0a", border: "1px solid rgba(255,255,255,0.1)" }}
            >
              <SelectItem value="all" className="text-white/60 text-xs focus:bg-white/5">All statuses</SelectItem>
              {["new", "email_collected", "sent", "error", "skipped"].map((s) => (
                <SelectItem key={s} value={s} className="capitalize text-white/60 text-xs focus:bg-white/5">{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Language toggle */}
          <div className="flex items-center rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {(["all", "pt", "en"] as const).map((l) => {
              const labels: Record<string, string> = { all: "Todos", pt: "Português", en: "English" };
              const active = lang === l;
              const borderRight = l === "en" ? undefined : "1px solid rgba(255,255,255,0.08)";
              return (
                <button
                  key={l}
                  type="button"
                  onClick={() => changeLang(l)}
                  className="h-8 px-3 text-[11px] font-medium transition-colors"
                  style={{
                    background: active ? "rgba(124,58,237,0.25)" : "rgba(255,255,255,0.03)",
                    color: active ? "#c4b5fd" : "rgba(255,255,255,0.4)",
                    borderRight,
                  }}
                >
                  {labels[l]}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-4 text-[12px]" style={{ color: "rgba(255,255,255,0.3)" }}>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="hover:text-white/60 disabled:opacity-25 transition-colors"
          >
            ← Prev
          </button>
          <span className="tabular-nums text-white/40">Page {page + 1}</span>
          <button
            type="button"
            disabled={filtered.length < PAGE_SIZE}
            onClick={() => setPage((p) => p + 1)}
            className="hover:text-white/60 disabled:opacity-25 transition-colors"
          >
            Next →
          </button>
        </div>
      </div>

      {/* Table */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{ border: "1px solid rgba(255,255,255,0.07)", background: "rgba(0,0,0,0.5)" }}
      >
        <Table>
          <TableHeader>
            <TableRow
              className="hover:bg-transparent"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", background: "rgba(255,255,255,0.02)" }}
            >
              {["Company", "Title", "Lang", "Email", "Status", "When"].map((h, i) => (
                <TableHead
                  key={h}
                  className={`text-[10px] font-semibold uppercase tracking-[0.12em] py-3 ${i === 0 ? "pl-6" : ""} ${i === 5 ? "pr-6" : ""}`}
                  style={{ color: "rgba(255,255,255,0.3)" }}
                >
                  {h}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>{renderRows()}</TableBody>
        </Table>
      </div>
    </div>
  );
}
