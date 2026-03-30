"use client";

import { useEffect, useState, useCallback } from "react";
import { ExternalLink, X, Check, Building2, MapPin, Clock } from "lucide-react";
import { getJobs, dismissJob, markApplied, type Job } from "@/lib/api";

const PAGE_SIZE = 24;

const COMPANIES = [
  "all",
  "Google", "Microsoft", "Meta", "Apple", "Amazon", "IBM", "Oracle",
  "SAP", "Dell", "Salesforce", "Nubank", "iFood", "Mercado Livre",
  "Stone", "C6Bank", "Inter", "PicPay", "Itaú", "Santander",
];

const STATUS_STYLES: Record<string, { dot: string; label: string }> = {
  new:     { dot: "rgba(255,255,255,0.3)",  label: "Nova" },
  applied: { dot: "#4ade80",               label: "Aplicada" },
  error:   { dot: "#f87171",               label: "Erro" },
  skipped: { dot: "rgba(255,255,255,0.12)", label: "Ignorada" },
};

function timeAgo(iso: string): string {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "agora";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export function JobsGrid() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [status, setStatus] = useState("all");
  const [company, setCompany] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);

  const debouncedSearch = useDebounce(search, 280);

  const load = useCallback(() => {
    setLoading(true);
    getJobs({
      status,
      company,
      search: debouncedSearch || undefined,
      limit: PAGE_SIZE,
      skip: page * PAGE_SIZE,
    })
      .then((data) => {
        setJobs(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, [status, company, debouncedSearch, page]);

  useEffect(() => { load(); }, [load]);

  function resetPage() { setPage(0); }

  async function handleApply(job: Job) {
    window.open(job.url, "_blank", "noopener,noreferrer");
    setJobs((prev) => prev.map((j) => j.id === job.id ? { ...j, status: "applied" } : j));
    markApplied(job.id).catch(() => {
      setJobs((prev) => prev.map((j) => j.id === job.id ? { ...j, status: job.status } : j));
    });
  }

  async function handleDismiss(job: Job) {
    setJobs((prev) => prev.filter((j) => j.id !== job.id));
    dismissJob(job.id).catch(() => {
      setJobs((prev) => [...prev, job]);
    });
  }

  const statusOptions = [
    { value: "all", label: "Todos" },
    { value: "new", label: "Novas" },
    { value: "applied", label: "Aplicadas" },
    { value: "skipped", label: "Ignoradas" },
    { value: "error", label: "Erros" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>

      {/* ── Toolbar ──────────────────────────────── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-3)",
        flexWrap: "wrap",
      }}>
        {/* Search */}
        <div style={{ position: "relative", flex: "1 1 240px", minWidth: 0 }}>
          <svg
            style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-faint)", pointerEvents: "none" }}
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="search"
            placeholder="Buscar por título…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); resetPage(); }}
            style={{
              width: "100%",
              height: "34px",
              paddingLeft: "32px",
              paddingRight: "var(--space-3)",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              color: "var(--text)",
              fontSize: "0.8125rem",
              outline: "none",
              transition: "border-color var(--ease)",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border)"; }}
          />
        </div>

        {/* Company filter */}
        <select
          value={company}
          onChange={(e) => { setCompany(e.target.value); resetPage(); }}
          style={{
            height: "34px",
            padding: "0 var(--space-3)",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            color: company === "all" ? "var(--text-muted)" : "var(--text)",
            fontSize: "0.8125rem",
            cursor: "pointer",
            outline: "none",
          }}
        >
          {COMPANIES.map((c) => (
            <option key={c} value={c} style={{ background: "#161614" }}>
              {c === "all" ? "Todas as empresas" : c}
            </option>
          ))}
        </select>

        {/* Status filter */}
        <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", overflow: "hidden" }}>
          {statusOptions.map((opt, i) => {
            const active = status === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => { setStatus(opt.value); resetPage(); }}
                style={{
                  height: "34px",
                  padding: "0 var(--space-3)",
                  fontSize: "0.75rem",
                  fontWeight: 500,
                  background: active ? "var(--surface-2)" : "var(--surface)",
                  color: active ? "var(--text)" : "var(--text-muted)",
                  borderRight: i < statusOptions.length - 1 ? "1px solid var(--border)" : undefined,
                  cursor: "pointer",
                  transition: "background var(--ease), color var(--ease)",
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>

        {/* Pagination */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            style={{
              height: "34px",
              width: "34px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              color: page === 0 ? "var(--text-faint)" : "var(--text-muted)",
              cursor: page === 0 ? "not-allowed" : "pointer",
              fontSize: "0.875rem",
            }}
          >
            ←
          </button>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
            {page + 1}
          </span>
          <button
            type="button"
            disabled={!hasMore}
            onClick={() => setPage((p) => p + 1)}
            style={{
              height: "34px",
              width: "34px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              color: !hasMore ? "var(--text-faint)" : "var(--text-muted)",
              cursor: !hasMore ? "not-allowed" : "pointer",
              fontSize: "0.875rem",
            }}
          >
            →
          </button>
        </div>
      </div>

      {/* ── Grid ─────────────────────────────────── */}
      {loading ? (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(min(320px, 100%), 1fr))",
          gap: "var(--space-3)",
        }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              style={{
                height: "140px",
                borderRadius: "var(--radius-lg)",
                background: "linear-gradient(90deg, var(--surface) 25%, var(--surface-2) 50%, var(--surface) 75%)",
                backgroundSize: "200% 100%",
                animation: "shimmer 1.6s ease-in-out infinite",
              }}
            />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "var(--space-16) var(--space-8)",
          gap: "var(--space-4)",
          color: "var(--text-muted)",
          textAlign: "center",
        }}>
          <Building2 size={32} style={{ color: "var(--text-faint)" }} />
          <div>
            <p style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text)" }}>Nenhuma vaga encontrada</p>
            <p style={{ fontSize: "0.8125rem", marginTop: "4px" }}>Tente outro filtro ou rode o scraper.</p>
          </div>
        </div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(min(320px, 100%), 1fr))",
          gap: "var(--space-3)",
        }}>
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} onApply={handleApply} onDismiss={handleDismiss} />
          ))}
        </div>
      )}

      <style>{`
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}

function JobCard({
  job,
  onApply,
  onDismiss,
}: {
  job: Job;
  onApply: (j: Job) => void;
  onDismiss: (j: Job) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const st = STATUS_STYLES[job.status] ?? STATUS_STYLES.new;
  const isApplied = job.status === "applied";

  return (
    <article
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3)",
        padding: "var(--space-4)",
        background: hovered ? "var(--surface-2)" : "var(--surface)",
        border: `1px solid ${hovered ? "rgba(255,255,255,0.12)" : "var(--border)"}`,
        borderRadius: "var(--radius-lg)",
        transition: "background var(--ease), border-color var(--ease)",
        cursor: "default",
      }}
    >
      {/* Top row: company + status dot */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <img
            src={`https://cdn.simpleicons.org/${job.company.toLowerCase().replace(/\s+/g, "")}`}
            alt=""
            width={16}
            height={16}
            style={{ opacity: 0.7, flexShrink: 0 }}
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
            loading="lazy"
          />
          <span style={{
            fontSize: "0.75rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            letterSpacing: "0.02em",
          }}>
            {job.company}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <span
            style={{
              width: "6px", height: "6px",
              borderRadius: "50%",
              background: st.dot,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: "0.6875rem", color: "var(--text-faint)" }}>{st.label}</span>
        </div>
      </div>

      {/* Title */}
      <h3 style={{
        fontSize: "0.9375rem",
        fontWeight: 600,
        color: "var(--text)",
        lineHeight: 1.3,
        letterSpacing: "-0.01em",
        flexGrow: 1,
      }}>
        {job.title}
      </h3>

      {/* Meta row */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)", flexWrap: "wrap" }}>
        {job.location && (
          <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            <MapPin size={11} />
            {job.location}
          </span>
        )}
        <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
          <Clock size={11} />
          {timeAgo(job.created_at)}
        </span>
        {job.language && (
          <span style={{
            fontSize: "0.6875rem",
            fontWeight: 600,
            padding: "1px 6px",
            borderRadius: "var(--radius-sm)",
            background: job.language === "pt" ? "rgba(251,191,36,0.1)" : "rgba(56,189,248,0.1)",
            color: job.language === "pt" ? "#fbbf24" : "#38bdf8",
          }}>
            {job.language.toUpperCase()}
          </span>
        )}
      </div>

      {/* Actions — visible on hover */}
      <div style={{
        display: "flex",
        gap: "var(--space-2)",
        opacity: hovered ? 1 : 0,
        transform: hovered ? "translateY(0)" : "translateY(4px)",
        transition: "opacity var(--ease), transform var(--ease)",
      }}>
        <button
          type="button"
          onClick={() => onApply(job)}
          disabled={isApplied}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "5px",
            flex: 1,
            height: "30px",
            justifyContent: "center",
            fontSize: "0.75rem",
            fontWeight: 600,
            borderRadius: "var(--radius-md)",
            background: isApplied ? "rgba(74,222,128,0.1)" : "var(--accent-subtle)",
            border: `1px solid ${isApplied ? "rgba(74,222,128,0.25)" : "var(--accent-border)"}`,
            color: isApplied ? "#4ade80" : "var(--accent)",
            cursor: isApplied ? "default" : "pointer",
            transition: "background var(--ease)",
          }}
        >
          {isApplied ? <Check size={11} /> : <ExternalLink size={11} />}
          {isApplied ? "Aplicada" : "Aplicar"}
        </button>
        <button
          type="button"
          aria-label="Ignorar vaga"
          onClick={() => onDismiss(job)}
          style={{
            width: "30px",
            height: "30px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "var(--radius-md)",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid var(--border)",
            color: "var(--text-faint)",
            cursor: "pointer",
            transition: "background var(--ease), color var(--ease)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(248,113,113,0.1)"; e.currentTarget.style.color = "#f87171"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.04)"; e.currentTarget.style.color = "var(--text-faint)"; }}
        >
          <X size={11} />
        </button>
      </div>
    </article>
  );
}
