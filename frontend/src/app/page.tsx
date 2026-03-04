import { getStats } from "@/lib/api";
import { StatsBar } from "@/components/stats-bar";
import { JobsTable } from "@/components/jobs-table";
import { ConfigPanel } from "@/components/config-panel";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const stats = await getStats().catch(() => ({
    total_sent_today: 0,
    total_sent_all: 0,
    errors_today: 0,
  }));

  return (
    <div className="min-h-screen">
      {/* ── Header ─────────────────────────────────────── */}
      <header
        className="sticky top-0 z-20 flex items-center justify-between h-16 px-8"
        style={{
          background: "rgba(0,0,0,0.75)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        {/* Planet logo + wordmark */}
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8 flex-shrink-0">
            {/* Planet body */}
            <div
              className="absolute inset-[5px] rounded-full bg-gradient-to-br from-violet-400 via-violet-600 to-indigo-800"
              style={{ boxShadow: "0 0 14px rgba(124,58,237,0.7), 0 0 4px rgba(124,58,237,0.9)" }}
            />
            {/* Ring */}
            <svg viewBox="0 0 32 32" className="absolute inset-0 w-full h-full" fill="none">
              <ellipse
                cx="16" cy="16" rx="13" ry="5"
                stroke="rgba(196,181,253,0.85)" strokeWidth="1.5"
                fill="none" transform="rotate(-28 16 16)"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <span className="text-[15px] font-bold text-white tracking-tight">JobScout</span>
        </div>

        <ConfigPanel />
      </header>

      {/* ── Stats ──────────────────────────────────────── */}
      <StatsBar initialStats={stats} />

      {/* ── Jobs ───────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-8 py-10">
        <div className="mb-8">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-violet-400 mb-2">
            Tracked opportunities
          </p>
          <h2 className="text-xl font-bold text-white">Jobs</h2>
          <p className="text-[13px] mt-1" style={{ color: "rgba(255,255,255,0.4)" }}>
            All scraped positions and their current status
          </p>
        </div>
        <JobsTable />
      </main>
    </div>
  );
}
