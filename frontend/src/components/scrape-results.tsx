"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ExternalLink, Eye, Loader2, Mail, Send, X } from "lucide-react";
import {
  getEmailPreview,
  sendSelectedJobs,
  type EmailPreview,
  type ScrapeResult,
} from "@/lib/api";

interface ScrapeResultsProps {
  readonly results: ScrapeResult[];
  readonly onDismiss: () => void;
}

const LANG_CLASS: Record<string, string> = {
  pt: "text-amber-400 bg-amber-400/10",
  en: "text-sky-400 bg-sky-400/10",
};

// ── Email preview modal ────────────────────────────────────────────────

function PreviewModal({
  jobId,
  company,
  title,
  onClose,
}: {
  readonly jobId: number;
  readonly company: string;
  readonly title: string;
  readonly onClose: () => void;
}) {
  const [preview, setPreview] = useState<EmailPreview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getEmailPreview(jobId)
      .then(setPreview)
      .catch(() => toast.error("Failed to load preview"))
      .finally(() => setLoading(false));
  }, [jobId]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.8)", backdropFilter: "blur(8px)" }}
    >
      <div
        className="relative w-full max-w-lg rounded-2xl flex flex-col"
        style={{
          background: "#080808",
          border: "1px solid rgba(255,255,255,0.1)",
          maxHeight: "80vh",
        }}
      >
        {/* Header */}
        <div
          className="flex items-start justify-between p-5"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
        >
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-violet-400 mb-1">
              Email preview
            </p>
            <p className="font-semibold text-white text-sm">{company}</p>
            <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.4)" }}>{title}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: "rgba(255,255,255,0.4)" }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {(() => {
            if (loading) {
              return (
                <div className="flex items-center gap-2 text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>
                  <Loader2 size={13} className="animate-spin" /> Loading…
                </div>
              );
            }
            if (!preview) return null;
            return (
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>Subject</p>
                  <p className="text-sm font-medium text-white bg-white/[0.04] rounded-lg px-3 py-2">{preview.subject}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>Body</p>
                  <pre
                    className="text-[12px] leading-relaxed whitespace-pre-wrap rounded-lg px-3 py-3"
                    style={{ color: "rgba(255,255,255,0.7)", background: "rgba(255,255,255,0.03)", fontFamily: "inherit" }}
                  >
                    {preview.body}
                  </pre>
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────

export function ScrapeResults({ results, onDismiss }: ScrapeResultsProps) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [sending, setSending] = useState(false);
  const [previewJob, setPreviewJob] = useState<ScrapeResult | null>(null);
  const [lang, setLang] = useState("all");

  const filteredResults = lang === "all" ? results : results.filter((r) => r.language === lang);
  const withEmail = filteredResults.filter((r) => r.email);
  const all = withEmail.map((r) => r.id);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) => (prev.size === all.length ? new Set() : new Set(all)));
  }

  async function handleSend() {
    if (selected.size === 0) return;
    setSending(true);
    try {
      const summary = await sendSelectedJobs(Array.from(selected));
      toast.success("Emails sent", {
        description: `Sent ${summary.sent} · Skipped ${summary.skipped} · Errors ${summary.errors}`,
        duration: 6000,
      });
      onDismiss();
    } catch {
      toast.error("Failed to send emails");
    } finally {
      setSending(false);
    }
  }

  if (results.length === 0) {
    return (
      <div
        className="rounded-2xl p-8 flex flex-col items-center gap-3 text-center"
        style={{ border: "1px solid rgba(255,255,255,0.07)", background: "rgba(255,255,255,0.02)" }}
      >
        <Mail size={32} style={{ color: "rgba(255,255,255,0.15)" }} />
        <p className="font-semibold text-white/40">No new jobs found</p>
        <p className="text-xs text-white/25">All jobs are already in the database</p>
        <button type="button" onClick={onDismiss} className="text-xs text-violet-400 hover:text-violet-300 mt-2">
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <>
      {previewJob && (
        <PreviewModal
          jobId={previewJob.id}
          company={previewJob.company}
          title={previewJob.title}
          onClose={() => setPreviewJob(null)}
        />
      )}

      <div
        className="rounded-2xl overflow-hidden"
        style={{ border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.04)" }}
      >
        {/* Toolbar */}
        <div
          className="flex items-center justify-between px-5 py-3"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.04)" }}
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="select-all"
                checked={selected.size === all.length && all.length > 0}
                onChange={toggleAll}
                className="w-4 h-4 accent-violet-500 cursor-pointer"
              />
              <label htmlFor="select-all" className="text-xs font-medium cursor-pointer" style={{ color: "rgba(255,255,255,0.75)" }}>
                {filteredResults.length} new {filteredResults.length === 1 ? "job" : "jobs"}
                {withEmail.length < filteredResults.length && (
                  <span style={{ color: "rgba(255,255,255,0.5)" }}> · {withEmail.length} with email</span>
                )}
              </label>
            </div>

            {/* Language toggle */}
            <div className="flex items-center rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
              {(["all", "pt", "en"] as const).map((l, i) => {
                const labels: Record<string, string> = { all: "Todos", pt: "Português", en: "English" };
                const active = lang === l;
                return (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setLang(l)}
                    className="h-7 px-2.5 text-[11px] font-medium transition-colors"
                    style={{
                      background: active ? "rgba(124,58,237,0.25)" : "rgba(255,255,255,0.03)",
                      color: active ? "#c4b5fd" : "rgba(255,255,255,0.4)",
                      borderRight: i < 2 ? "1px solid rgba(255,255,255,0.08)" : undefined,
                    }}
                  >
                    {labels[l]}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onDismiss}
              className="text-xs px-3 py-1.5 rounded-lg transition-colors"
              style={{ color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.15)" }}
            >
              Dismiss
            </button>
            <button
              type="button"
              onClick={handleSend}
              disabled={sending || selected.size === 0}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-semibold bg-violet-600 hover:bg-violet-500 text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {sending ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              {sending ? "Sending…" : `Send selected (${selected.size})`}
            </button>
          </div>
        </div>

        {/* Job list */}
        <div className="divide-y" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          {filteredResults.map((job) => {
            const hasEmail = !!job.email;
            return (
              <div
                key={job.id}
                className="flex items-center gap-4 px-5 py-4 hover:bg-white/[0.03] transition-colors"
              >
                <input
                  type="checkbox"
                  id={`job-${job.id}`}
                  checked={selected.has(job.id)}
                  onChange={() => toggle(job.id)}
                  disabled={!hasEmail}
                  className="w-4 h-4 accent-violet-500 cursor-pointer disabled:cursor-not-allowed flex-shrink-0"
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{job.company}</span>
                    {job.language && (
                      <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${LANG_CLASS[job.language] ?? ""}`}>
                        {job.language}
                      </span>
                    )}
                    {!hasEmail && (
                      <span className="text-[10px] font-semibold text-amber-400/70 bg-amber-400/10 px-1.5 py-0.5 rounded">no email</span>
                    )}
                  </div>
                  <p className="text-sm mt-0.5 truncate font-medium" style={{ color: "rgba(255,255,255,0.75)" }}>{job.title}</p>
                  {job.email && (
                    <p className="text-[11px] mt-0.5 truncate" style={{ color: "rgba(255,255,255,0.5)" }}>{job.email}</p>
                  )}
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {hasEmail && (
                    <button
                      type="button"
                      onClick={() => setPreviewJob(job)}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-colors"
                      style={{ color: "rgba(255,255,255,0.7)", border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.04)" }}
                      title="Preview email"
                    >
                      <Eye size={11} /> Preview
                    </button>
                  )}
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center w-7 h-7 rounded-lg transition-colors"
                    style={{ color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.04)" }}
                    title="Open job"
                  >
                    <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
