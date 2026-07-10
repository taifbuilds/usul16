"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export function SearchBox({ defaultValue = "", size = "md" }: { defaultValue?: string; size?: "md" | "lg" }) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    if (trimmed) router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  const padding = size === "lg" ? "px-5 py-3 text-base" : "px-3 py-1.5 text-sm";

  return (
    <form onSubmit={handleSubmit} role="search" className="flex w-full gap-2">
      <input
        type="search"
        name="q"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Search hadith text or a book title…"
        className={`flex-1 rounded-full border border-border bg-surface ${padding} outline-none focus:border-accent focus:ring-1 focus:ring-accent`}
      />
      <button
        type="submit"
        className={`rounded-full bg-accent ${padding} font-medium text-accent-foreground hover:opacity-90`}
      >
        Search
      </button>
    </form>
  );
}
