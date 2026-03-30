"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Loader2, RefreshCw } from "lucide-react";
import { getStats, scrapePipeline, type JobStats } from "@/lib/api";

interface StatsBarProps {
  readonly initialStats: JobStats;
}

const STAT_ITEMS = [
  { key: "total_jobs" as const,         label: "Total vagas" },
  { key: "new_today" as const,           label: "Novas hoje" },
  { key: "companies_tracked" as const,   label: "Empresas" },
  { key: "errors_today" as const,        label: "Erros hoje" },
] as const;

export function StatsBar({ initialStats }: StatsBarProps) {
  const [stats, setStats] = useState<JobStats>(initialStats);
  const [loading, setLoading] = useState(false);

  async function handleScrape() {
    setLoading(true);
    try {
      const jobs = await scrapePipeline();
      const fresh = await getStats();
      setStats(fresh);
      if (jobs.length === 0) {
        toast.info("Nenhuma vaga nova", { description: "Tudo já está na base." });
      } else {
        toast.success(`${jobs.length} vaga${jobs.length === 1 ? "" : "s"} coletada${jobs.length === 1 ? "" : "s"}`);
      }
    } catch {
      toast.error("Scrape falhou", { description: "Verifique os logs do backend." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "var(--space-8) var(--space-8) 0",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "var(--space-6)",
      }}>
        {/* Stats row */}
        <div style={{ display: "flex", gap: "var(--space-8)", alignItems: "baseline" }}>
          {STAT_ITEMS.map(({ key, label }) => {
            const value = stats[key];
            const isError = key === "errors_today" && value > 0;
            return (
              <div key={key} style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  letterSpacing: "-0.03em",
                  fontVariantNumeric: "tabular-nums",
                  lineHeight: 1,
                  color: isError ? "var(--status-err)" : "var(--text)",
                }}>
                  {value}
                </span>
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Scrape button */}
        <button
          type="button"
          onClick={handleScrape}
          disabled={loading}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "0 var(--space-4)",
            height: "34px",
            background: "var(--accent-subtle)",
            border: "1px solid var(--accent-border)",
            borderRadius: "var(--radius-md)",
            color: "var(--accent)",
            fontSize: "0.8125rem",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.5 : 1,
            transition: "background var(--ease), border-color var(--ease)",
          }}
          onMouseEnter={(e) => {
            if (!loading) (e.currentTarget as HTMLButtonElement).style.background = "rgba(217,119,6,0.2)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "var(--accent-subtle)";
          }}
        >
          {loading
            ? <Loader2 size={13} style={{ animation: "spin 0.8s linear infinite" }} />
            : <RefreshCw size={13} />}
          {loading ? "Coletando…" : "Atualizar"}
        </button>
      </div>

      {/* Divider */}
      <div style={{ height: "1px", background: "var(--divider)" }} />
    </section>
  );
}
