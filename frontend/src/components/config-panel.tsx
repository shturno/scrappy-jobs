"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
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
      .then((c) => {
        setConfig(c);
        setKeywords(c.search_keywords);
        setCities(c.search_cities);
      })
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
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          className="border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
        >
          ⚙ Config
        </Button>
      </SheetTrigger>
      <SheetContent className="border-zinc-800 bg-zinc-950 text-zinc-100 w-[360px]">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-zinc-100">Pipeline Config</SheetTitle>
        </SheetHeader>

        {config == null ? (
          <p className="text-zinc-500 text-sm">Loading…</p>
        ) : (
          <div className="flex flex-col gap-6">
            <TagsInput
              label="Search keywords"
              tags={keywords}
              onChange={setKeywords}
              placeholder="desenvolvedor backend, react…"
            />

            <TagsInput
              label="Search cities"
              tags={cities}
              onChange={setCities}
              placeholder="São Paulo, Curitiba…"
            />

            <div className="rounded-md border border-zinc-800 bg-zinc-900/50 p-3 space-y-1 text-sm text-zinc-400">
              <p><span className="text-zinc-500">Daily limit:</span> {config.daily_limit}</p>
              <p><span className="text-zinc-500">Sender:</span> {config.sender_name || "—"}</p>
              <p><span className="text-zinc-500">LinkedIn:</span> {config.sender_linkedin || "—"}</p>
              <p><span className="text-zinc-500">GitHub:</span> {config.sender_github || "—"}</p>
              <p><span className="text-zinc-500">Portfolio:</span> {config.sender_portfolio || "—"}</p>
            </div>

            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              {saving ? "Saving…" : "Save config"}
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
