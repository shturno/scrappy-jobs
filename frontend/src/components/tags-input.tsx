"use client";

import { KeyboardEvent, useState } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface TagsInputProps {
  readonly label: string;
  readonly tags: string[];
  readonly onChange: (tags: string[]) => void;
  readonly placeholder?: string;
}

export function TagsInput({ label, tags, onChange, placeholder }: TagsInputProps) {
  const [draft, setDraft] = useState("");

  function addTag() {
    const trimmed = draft.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setDraft("");
  }

  function removeTag(tag: string) {
    onChange(tags.filter((t) => t !== tag));
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    }
    if (e.key === "Backspace" && draft === "" && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm text-zinc-400">{label}</label>
      <div className="flex flex-wrap gap-1.5 p-2 rounded-md border border-zinc-700 bg-zinc-900 min-h-[42px]">
        {tags.map((tag) => (
          <Badge
            key={tag}
            className="bg-zinc-700 text-zinc-200 hover:bg-zinc-700 gap-1 pr-1"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="ml-1 rounded-sm hover:text-red-400 transition-colors leading-none"
            >
              ×
            </button>
          </Badge>
        ))}
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={addTag}
          placeholder={tags.length === 0 ? (placeholder ?? "Type and press Enter") : ""}
          className="flex-1 min-w-[120px] border-0 bg-transparent p-0 text-zinc-200 placeholder:text-zinc-600 focus-visible:ring-0 h-auto"
        />
      </div>
    </div>
  );
}
