"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getStats, runPipeline, type EmailStats, type PipelineSummary } from "@/lib/api";

interface StatsBarProps {
  readonly initialStats: EmailStats;
}

export function StatsBar({ initialStats }: StatsBarProps) {
  const [stats, setStats] = useState<EmailStats>(initialStats);
  const [running, setRunning] = useState(false);

  async function handleRun() {
    setRunning(true);
    try {
      const summary: PipelineSummary = await runPipeline();
      const fresh = await getStats();
      setStats(fresh);
      toast.success("Pipeline completed", {
        description: `Scraped ${summary.scraped} · Emails found ${summary.emails_found} · Sent ${summary.sent} · Errors ${summary.errors}`,
        duration: 6000,
      });
    } catch {
      toast.error("Pipeline failed", { description: "Check the backend logs." });
    } finally {
      setRunning(false);
    }
  }

  const sentPercent = Math.min((stats.total_sent_today / 30) * 100, 100);

  return (
    <div className="flex flex-wrap items-center gap-4">
      <Card className="flex-1 min-w-[160px] border-zinc-800 bg-zinc-900/60 backdrop-blur">
        <CardContent className="p-4">
          <p className="text-xs text-zinc-400 mb-1">Sent today</p>
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-white">{stats.total_sent_today}</span>
            <span className="text-zinc-500 text-sm mb-0.5">/ 30</span>
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${sentPercent}%` }}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="flex-1 min-w-[160px] border-zinc-800 bg-zinc-900/60 backdrop-blur">
        <CardContent className="p-4">
          <p className="text-xs text-zinc-400 mb-1">All time sent</p>
          <span className="text-2xl font-bold text-white">{stats.total_sent_all}</span>
        </CardContent>
      </Card>

      <Card className="flex-1 min-w-[160px] border-zinc-800 bg-zinc-900/60 backdrop-blur">
        <CardContent className="p-4">
          <p className="text-xs text-zinc-400 mb-1">Errors today</p>
          <span
            className={`text-2xl font-bold ${stats.errors_today > 0 ? "text-red-400" : "text-white"}`}
          >
            {stats.errors_today}
          </span>
        </CardContent>
      </Card>

      <Button
        onClick={handleRun}
        disabled={running}
        className="h-[72px] px-6 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-all duration-200 disabled:opacity-50"
      >
        {running ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            {" Running…"}
          </span>
        ) : (
          "▶ Run now"
        )}
      </Button>
    </div>
  );
}
