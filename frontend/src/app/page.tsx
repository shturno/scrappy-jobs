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
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold tracking-tight text-white">JobScout</span>
            <span className="text-xs text-zinc-500 border border-zinc-800 rounded px-2 py-0.5">
              MVP
            </span>
          </div>
          <ConfigPanel />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 flex flex-col gap-8">
        {/* Stats bar */}
        <section>
          <StatsBar initialStats={stats} />
        </section>

        {/* Jobs table */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">
              Jobs
            </h2>
          </div>
          <JobsTable />
        </section>
      </main>
    </div>
  );
}
