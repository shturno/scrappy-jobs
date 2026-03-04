"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Rocket, Loader2, Send, Star, AlertTriangle } from "lucide-react";
import { getStats, runPipeline, type EmailStats, type PipelineSummary } from "@/lib/api";

interface StatsBarProps {
  readonly initialStats: EmailStats;
}

const CARDS = [
  {
    key: "sent_today" as const,
    label: "Sent today",
    icon: Send,
    accent: "#7c3aed",
    accentAlpha: "rgba(124,58,237,0.15)",
    glow: "rgba(124,58,237,0.5)",
  },
  {
    key: "all_time" as const,
    label: "All time",
    icon: Star,
    accent: "#10b981",
    accentAlpha: "rgba(16,185,129,0.1)",
    glow: "rgba(16,185,129,0.4)",
  },
  {
    key: "errors" as const,
    label: "Errors today",
    icon: AlertTriangle,
    accent: "#f43f5e",
    accentAlpha: "rgba(244,63,94,0.1)",
    glow: "rgba(244,63,94,0.4)",
  },
];

export function StatsBar({ initialStats }: StatsBarProps) {
  const [stats, setStats] = useState<EmailStats>(initialStats);
  const [running, setRunning] = useState(false);

  async function handleRun() {
    setRunning(true);
    try {
      const summary: PipelineSummary = await runPipeline();
      const fresh = await getStats();
      setStats(fresh);
      toast.success("Mission complete", {
        description: `Scraped ${summary.scraped} · Found ${summary.emails_found} · Sent ${summary.sent} · Errors ${summary.errors}`,
        duration: 7000,
      });
    } catch {
      toast.error("Mission failed", { description: "Check the backend logs." });
    } finally {
      setRunning(false);
    }
  }

  const sentPercent = Math.min((stats.total_sent_today / 30) * 100, 100);

  function getValue(key: typeof CARDS[number]["key"]): number {
    if (key === "sent_today") return stats.total_sent_today;
    if (key === "all_time") return stats.total_sent_all;
    return stats.errors_today;
  }

  return (
    <section className="relative max-w-5xl mx-auto px-8 py-10">
      {/* Orbital ring — decorative, centered behind cards */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <svg viewBox="0 0 700 200" className="w-[700px] h-[200px]" fill="none" aria-hidden="true">
          <ellipse cx="350" cy="100" rx="340" ry="88" stroke="rgba(124,58,237,0.18)" strokeWidth="1.5" />
          <ellipse cx="350" cy="100" rx="270" ry="62" stroke="rgba(124,58,237,0.10)" strokeWidth="0.8" />
          <ellipse cx="350" cy="100" rx="175" ry="38" stroke="rgba(124,58,237,0.07)" strokeWidth="0.5" />
        </svg>
      </div>

      {/* Section header */}
      <div className="flex items-center justify-between mb-8 relative">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-violet-400 mb-1">
            Mission status
          </p>
          <h2 className="text-lg font-bold text-white">Overview</h2>
        </div>

        <button
          type="button"
          onClick={handleRun}
          disabled={running}
          className="flex items-center gap-2 px-4 h-9 rounded-lg font-semibold text-[13px] text-white transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            background: running ? "rgba(124,58,237,0.5)" : "rgba(124,58,237,0.9)",
            border: "1px solid rgba(124,58,237,0.6)",
            boxShadow: running ? "none" : "0 0 16px rgba(124,58,237,0.35), inset 0 1px 0 rgba(255,255,255,0.1)",
          }}
          onMouseEnter={(e) => {
            if (!running) (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 24px rgba(124,58,237,0.5), inset 0 1px 0 rgba(255,255,255,0.12)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 16px rgba(124,58,237,0.35), inset 0 1px 0 rgba(255,255,255,0.1)";
          }}
        >
          {running
            ? <Loader2 size={14} className="animate-spin" />
            : <Rocket size={14} />}
          {running ? "Launching…" : "Launch pipeline"}
        </button>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-3 gap-5 relative">
        {CARDS.map(({ key, label, icon: Icon, accent, accentAlpha, glow }) => {
          const value = getValue(key);
          const isError = key === "errors" && value > 0;

          return (
            <output
              key={key}
              aria-label={`${label}: ${value}`}
              className="relative rounded-2xl p-6 overflow-hidden transition-all duration-200 block"
              style={{
                background: accentAlpha,
                border: `1px solid ${accent}25`,
              }}
            >
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[2px] rounded-t-2xl" style={{ background: accent, opacity: 0.7 }} />

              {/* Label row */}
              <div className="flex items-center justify-between mb-5">
                <span className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: `${accent}cc` }}>
                  {label}
                </span>
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ background: `${accent}20` }}
                >
                  <Icon size={13} style={{ color: accent }} />
                </div>
              </div>

              {/* Number */}
              <div className="flex items-baseline gap-2">
                <span
                  className="text-6xl font-black leading-none tabular-nums"
                  style={{
                    color: isError ? "#f43f5e" : "#fff",
                    letterSpacing: "-0.04em",
                    textShadow: isError ? `0 0 20px rgba(244,63,94,0.5)` : `0 0 30px ${glow}`,
                  }}
                >
                  {value}
                </span>
                {key === "sent_today" && (
                  <span className="text-lg font-medium" style={{ color: "rgba(255,255,255,0.3)" }}>
                    / 30
                  </span>
                )}
              </div>

              {/* Progress (sent today only) */}
              {key === "sent_today" && (
                <div className="mt-5 h-[3px] rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.08)" }}>
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${sentPercent}%`, background: accent, boxShadow: `0 0 8px ${glow}` }}
                  />
                </div>
              )}
            </output>
          );
        })}
      </div>
    </section>
  );
}
