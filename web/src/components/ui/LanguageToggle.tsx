"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";

// Interface-language toggle. Persists the choice in a cookie so the server
// renders the right dictionary and <html dir/lang> on the next request; flips
// the document direction immediately so the switch feels instant, then
// refreshes the server components in place (no navigation, URL unchanged).
export function LanguageToggle({ locale, className = "" }: { locale: Locale; className?: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const next: Locale = locale === "ar" ? "en" : "ar";
  const label = next === "ar" ? "العربية" : "English";
  const aria = next === "ar" ? "التبديل إلى العربية" : "Switch to English";

  function switchTo() {
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    const root = document.documentElement;
    root.lang = next;
    root.dir = next === "ar" ? "rtl" : "ltr";
    startTransition(() => router.refresh());
  }

  return (
    <button
      type="button"
      onClick={switchTo}
      aria-label={aria}
      data-pending={pending ? "" : undefined}
      className={`inline-flex h-11 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm font-semibold text-foreground/80 transition hover:border-accent hover:text-accent data-[pending]:opacity-60 ${className}`}
    >
      <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-[18px] w-[18px]">
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18" />
      </svg>
      <span>{label}</span>
    </button>
  );
}
