"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Settings2, Save, Loader2 } from "lucide-react";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet";
import { TagsInput } from "@/components/tags-input";
import { getConfig, updateConfig, type AppConfig } from "@/lib/api";

export function ConfigPanel() {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    getConfig()
      .then((c) => { setConfig(c); setKeywords(c.search_keywords); setCities(c.search_cities); })
      .catch(() => toast.error("Failed to load config"));
  }, [open]);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateConfig({ search_keywords: keywords, search_cities: cities });
      setConfig(updated);
      toast.success("Config saved");
      setOpen(false);
    } catch {
      toast.error("Failed to save config");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-3 h-8 rounded-lg text-[12px] font-medium transition-all duration-150"
        style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.1)",
          color: "rgba(255,255,255,0.5)",
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLButtonElement;
          el.style.background = "rgba(255,255,255,0.07)";
          el.style.borderColor = "rgba(255,255,255,0.18)";
          el.style.color = "rgba(255,255,255,0.85)";
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLButtonElement;
          el.style.background = "rgba(255,255,255,0.04)";
          el.style.borderColor = "rgba(255,255,255,0.1)";
          el.style.color = "rgba(255,255,255,0.5)";
        }}
      >
        <Settings2 size={13} />
        Config
      </button>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent
          className="flex flex-col p-0 gap-0 w-[380px]"
          style={{
            background: "#000",
            borderLeft: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          {/* Header */}
          <SheetHeader
            className="px-6 pt-7 pb-6"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
          >
            <div className="flex items-center gap-3 mb-1">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.3)" }}
              >
                <Settings2 size={14} className="text-violet-400" />
              </div>
              <SheetTitle className="text-[15px] font-bold text-white">Config</SheetTitle>
            </div>
            <SheetDescription className="text-[12px]" style={{ color: "rgba(255,255,255,0.35)" }}>
              Keywords and cities for the Gupy scraper. Changes apply on the next launch.
            </SheetDescription>
          </SheetHeader>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
            {config == null ? (
              <div className="flex items-center gap-2 text-[13px]" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Loader2 size={13} className="animate-spin text-violet-500" />
                Loading…
              </div>
            ) : (
              <>
                <section className="space-y-3">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-400">Keywords</p>
                    <p className="text-[11px] mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
                      Job titles to search on Gupy
                    </p>
                  </div>
                  <TagsInput label="" tags={keywords} onChange={setKeywords} placeholder="React Developer, Backend…" />
                </section>

                <section className="space-y-3">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-400">Cities</p>
                    <p className="text-[11px] mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
                      Use &quot;Remoto&quot; for remote listings
                    </p>
                  </div>
                  <TagsInput label="" tags={cities} onChange={setCities} placeholder="São Paulo, Remoto…" />
                </section>

                <section style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "24px" }}>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-400 mb-4">Sender</p>
                  <div className="space-y-0 rounded-xl overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
                    {[
                      ["Name", config.sender_name],
                      ["Daily limit", `${config.daily_limit} / day`],
                      ["LinkedIn", config.sender_linkedin],
                      ["GitHub", config.sender_github],
                    ].map(([k, v], i, arr) => (
                      <div
                        key={k}
                        className="flex justify-between items-center px-4 py-3"
                        style={{
                          borderBottom: i < arr.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
                        }}
                      >
                        <span className="text-[11px]" style={{ color: "rgba(255,255,255,0.3)" }}>{k}</span>
                        <span className="text-[11px] text-white/60 truncate max-w-[190px] text-right">{v || "—"}</span>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-5" style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || config == null || keywords.length === 0 || cities.length === 0}
              className="w-full flex items-center justify-center gap-2 h-10 rounded-xl font-semibold text-[13px] text-white transition-all duration-150 disabled:opacity-40"
              style={{
                background: "rgba(124,58,237,0.9)",
                border: "1px solid rgba(124,58,237,0.5)",
                boxShadow: "0 0 16px rgba(124,58,237,0.3)",
              }}
            >
              {saving
                ? <><Loader2 size={13} className="animate-spin" />Saving…</>
                : <><Save size={13} />Save config</>}
            </button>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
