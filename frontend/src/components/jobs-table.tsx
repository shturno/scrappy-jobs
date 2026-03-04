"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { getJobs, type Job } from "@/lib/api";

const PAGE_SIZE = 20;

const STATUS_STYLES: Record<string, string> = {
  new: "bg-zinc-700 text-zinc-200 hover:bg-zinc-700",
  email_collected: "bg-blue-900/60 text-blue-300 hover:bg-blue-900/60",
  sent: "bg-emerald-900/60 text-emerald-300 hover:bg-emerald-900/60",
  error: "bg-red-900/60 text-red-300 hover:bg-red-900/60",
  skipped: "bg-zinc-800 text-zinc-400 hover:bg-zinc-800",
};

const LANG_STYLES: Record<string, string> = {
  pt: "bg-green-900/50 text-green-300 hover:bg-green-900/50",
  en: "bg-indigo-900/50 text-indigo-300 hover:bg-indigo-900/50",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });
}

export function JobsTable() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getJobs({ status, limit: PAGE_SIZE, offset: page * PAGE_SIZE })
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, [status, page]);

  function renderRows() {
    if (loading) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center text-zinc-500 py-12">
            Loading…
          </TableCell>
        </TableRow>
      );
    }
    if (jobs.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center text-zinc-500 py-12">
            No jobs found
          </TableCell>
        </TableRow>
      );
    }
    return jobs.map((job) => (
      <TableRow
        key={job.id}
        className="border-zinc-800 hover:bg-zinc-900/40 transition-colors cursor-pointer"
        onClick={() => window.open(job.url, "_blank")}
      >
        <TableCell className="text-zinc-200 font-medium">{job.company}</TableCell>
        <TableCell className="text-zinc-300 max-w-[200px] truncate">{job.title}</TableCell>
        <TableCell>
          {job.language && (
            <Badge className={`text-xs uppercase ${LANG_STYLES[job.language] ?? ""}`}>
              {job.language}
            </Badge>
          )}
        </TableCell>
        <TableCell className="text-zinc-400 text-sm max-w-[180px] truncate">
          {job.email ?? <span className="text-zinc-600">—</span>}
        </TableCell>
        <TableCell>
          <Badge className={`text-xs capitalize ${STATUS_STYLES[job.status] ?? ""}`}>
            {job.status}
          </Badge>
        </TableCell>
        <TableCell className="text-zinc-500 text-sm">
          {formatDate(job.created_at)}
        </TableCell>
      </TableRow>
    ));
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <Select value={status} onValueChange={(v) => { setStatus(v); setPage(0); }}>
          <SelectTrigger className="w-[160px] border-zinc-700 bg-zinc-900 text-zinc-200">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent className="border-zinc-700 bg-zinc-900 text-zinc-200">
            {["all", "new", "email_collected", "sent", "error", "skipped"].map((s) => (
              <SelectItem key={s} value={s} className="capitalize">
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
          >
            ← Prev
          </Button>
          <span>Page {page + 1}</span>
          <Button
            variant="outline"
            size="sm"
            disabled={jobs.length < PAGE_SIZE}
            onClick={() => setPage((p) => p + 1)}
            className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
          >
            Next →
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-zinc-800 overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-900/80">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400">Company</TableHead>
              <TableHead className="text-zinc-400">Title</TableHead>
              <TableHead className="text-zinc-400 w-16">Lang</TableHead>
              <TableHead className="text-zinc-400">Email</TableHead>
              <TableHead className="text-zinc-400 w-28">Status</TableHead>
              <TableHead className="text-zinc-400 w-24">Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>{renderRows()}</TableBody>
        </Table>
      </div>
    </div>
  );
}
