import { getStats } from "@/lib/api";
import { StatsBar } from "@/components/stats-bar";
import { JobsGrid } from "@/components/jobs-grid";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const stats = await getStats().catch(() => ({
    total_jobs: 0,
    new_today: 0,
    errors_today: 0,
    companies_tracked: 0,
  }));

  return (
    <div style={{ minHeight: "100dvh", background: "var(--bg)" }}>
      {/* ── Header ─────────────────────────────────────── */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "56px",
          padding: "0 var(--space-8)",
          background: "rgba(15,15,14,0.85)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid var(--divider)",
        }}
      >
        {/* Logo + wordmark */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <svg
            width="22" height="22" viewBox="0 0 22 22" fill="none"
            aria-label="Scrappy Jobs logo"
            style={{ color: "var(--accent)" }}
          >
            <circle cx="11" cy="11" r="3.5" fill="currentColor" />
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.2" strokeDasharray="2.5 2" opacity="0.6" />
            <circle cx="11" cy="11" r="10" stroke="currentColor" strokeWidth="0.8" opacity="0.25" />
          </svg>
          <span style={{
            fontSize: "0.9375rem",
            fontWeight: 600,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}>
            scrappy<span style={{ color: "var(--accent)" }}>.jobs</span>
          </span>
        </div>

        <span style={{
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          fontVariantNumeric: "tabular-nums",
        }}>
          uso pessoal
        </span>
      </header>

      {/* ── Stats ──────────────────────────────────────── */}
      <StatsBar initialStats={stats} />

      {/* ── Jobs ───────────────────────────────────────── */}
      <main style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-8) var(--space-16)",
      }}>
        <div style={{ marginBottom: "var(--space-6)" }}>
          <h2 style={{
            fontSize: "1.0625rem",
            fontWeight: 600,
            color: "var(--text)",
            letterSpacing: "-0.01em",
          }}>
            Vagas abertas
          </h2>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "2px" }}>
            Todas as posições coletadas pelos scrapers
          </p>
        </div>
        <JobsGrid />
      </main>
    </div>
  );
}
