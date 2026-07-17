"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

type Theme = "dark" | "light";

/** No-flash init: runs before paint to set data-theme from storage / OS. */
export const themeInitScript = `(function(){try{var t=localStorage.getItem('usul16-theme-v2')||'light';document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`;

export function ThemeToggle({ className = "" }: { className?: string }) {
  const reduceMotion = useReducedMotion();
  // Default to the SSR theme (dark) so an icon always shows; correct to the
  // real, already-applied theme on mount (the init script set data-theme
  // before paint, so this only diverges for light-preferring visitors).
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const current = (document.documentElement.getAttribute("data-theme") as Theme) || "light";
      setTheme((prev) => (prev === current ? prev : current));
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  function toggle() {
    const next: Theme = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("usul16-theme-v2", next);
    } catch {
      /* storage may be unavailable; the in-page toggle still works */
    }
  }

  const isLight = theme === "light";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isLight ? "Switch to dark theme" : "Switch to light theme"}
      className={`relative grid h-11 w-11 place-items-center rounded-md border border-border bg-surface text-foreground/80 transition hover:border-accent hover:text-accent ${className}`}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme ?? "unset"}
          initial={reduceMotion ? { opacity: 0 } : { opacity: 0, rotate: -90, scale: 0.5 }}
          animate={{ opacity: 1, rotate: 0, scale: 1 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, rotate: 90, scale: 0.5 }}
          transition={{ duration: reduceMotion ? 0 : 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="absolute"
        >
          {isLight ? (
            /* moon (offering the dark switch) */
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-[18px] w-[18px]">
              <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
            </svg>
          ) : (
            /* sun (offering the light switch) */
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-[18px] w-[18px]">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
            </svg>
          )}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
