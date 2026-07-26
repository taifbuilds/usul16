"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export function SearchBox({
  defaultValue = "",
  size = "md",
  placeholder = "Search Arabic text, translations, or a book…",
  submitLabel = "Search",
  ariaLabel = "Search the hadith corpus",
}: {
  defaultValue?: string;
  size?: "md" | "lg";
  placeholder?: string;
  submitLabel?: string;
  ariaLabel?: string;
}) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    if (trimmed) router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  const lg = size === "lg";
  const fieldPad = lg ? "h-14 ps-12 pe-3 text-base" : "h-11 ps-10 pe-3 text-sm";
  const iconPos = lg ? "start-4" : "start-3.5";
  const btnPad = lg ? "px-6 text-base" : "px-4 text-sm";

  return (
    <form onSubmit={handleSubmit} role="search" className={`group flex w-full items-stretch gap-2 ${lg ? "flex-col sm:flex-row" : ""}`}>
      <div className="relative min-w-0 flex-1">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          className={`pointer-events-none absolute top-1/2 ${iconPos} h-[18px] w-[18px] -translate-y-1/2 text-muted transition-colors group-focus-within:text-accent`}
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.2-3.2" />
        </svg>
        <input
          type="search"
          name="q"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          aria-label={ariaLabel}
          className={`w-full rounded-md border border-border bg-surface ${fieldPad} text-foreground outline-none transition-[border-color,box-shadow] duration-200 placeholder:text-muted focus:border-accent focus:shadow-[0_0_0_2px_var(--ring-soft)]`}
        />
      </div>
      <button
        type="submit"
        className={`inline-flex min-h-11 items-center justify-center rounded-md bg-accent ${btnPad} py-2.5 font-semibold text-accent-foreground transition-[background-color,transform] duration-200 hover:bg-accent-strong active:scale-[0.985] ${lg ? "h-12 sm:h-auto" : ""}`}
      >
        <span>{submitLabel}</span>
        {lg ? (
          <svg aria-hidden viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="ms-2 h-4 w-4 rtl:-scale-x-100">
            <path d="M4 10h12M12 6l4 4-4 4" />
          </svg>
        ) : null}
      </button>
    </form>
  );
}
