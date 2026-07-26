"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LanguageToggle } from "@/components/ui/LanguageToggle";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { amiri } from "@/lib/fonts";

export function SiteHeader({ locale, nav }: { locale: Locale; nav: Dictionary["nav"] }) {
  const pathname = usePathname();
  const reduce = useReducedMotion();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = [
    { href: "/books", label: nav.read, detail: nav.readDetail },
    { href: "/search", label: nav.find, detail: nav.findDetail },
    { href: "/graph", label: nav.investigate, detail: nav.investigateDetail },
  ];

  function isActive(href: string) {
    return pathname === href || (href !== "/" && pathname.startsWith(href));
  }

  useEffect(() => {
    if (!menuOpen) return;
    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  return (
    <>
      <a href="#main-content" className="skip-link">{nav.skip}</a>
      <header className="sticky top-0 z-50 border-b border-border bg-background/96 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-[90rem] items-center gap-1.5 px-3 sm:h-[4.5rem] sm:gap-4 sm:px-6 lg:px-8">
          <Link href="/" className="group flex min-w-0 items-center gap-2.5 whitespace-nowrap sm:gap-3" aria-label="Usul16 home">
            <span className="brand-mark" aria-hidden>
              <span className={`${amiri.className} text-base leading-none`}>١٦</span>
            </span>
            <span className="flex flex-col leading-none">
              <span className="font-serif text-lg font-semibold text-foreground sm:text-xl">Usul16</span>
              <span className="mt-1 hidden text-xs font-semibold text-muted sm:block">{nav.brandSub}</span>
            </span>
          </Link>

          <nav className="ms-3 hidden h-full items-stretch lg:flex" aria-label={nav.primaryNav}>
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(link.href) ? "page" : undefined}
                className={`relative flex min-w-32 flex-col justify-center border-x border-transparent px-5 transition-colors ${
                  isActive(link.href) ? "bg-surface-2 text-accent" : "text-muted hover:bg-surface-2 hover:text-foreground"
                }`}
              >
                <span className="text-sm font-semibold">{link.label}</span>
                <span className="mt-0.5 text-xs font-medium opacity-80">{link.detail}</span>
                {isActive(link.href) ? <span className="absolute inset-x-0 bottom-0 h-0.5 bg-accent" /> : null}
              </Link>
            ))}
          </nav>

          <div className="ms-auto flex shrink-0 items-center gap-1.5 sm:gap-2">
            <Link
              href="/about"
              className={`hidden min-h-11 items-center px-3 text-sm font-medium transition-colors sm:inline-flex ${
                isActive("/about") ? "text-accent" : "text-muted hover:text-foreground"
              }`}
            >
              {nav.about}
            </Link>
            <LanguageToggle locale={locale} className="h-10 max-sm:w-10 max-sm:justify-center max-sm:px-0 sm:h-11" />
            <ThemeToggle className="h-10 w-10 sm:h-11 sm:w-11" />
            <Link
              href="/search"
              className="hidden min-h-11 items-center gap-2 rounded-md border border-border bg-surface px-3.5 text-sm font-semibold text-foreground transition-colors hover:border-accent hover:text-accent md:inline-flex lg:hidden xl:inline-flex"
            >
              <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
                <circle cx="11" cy="11" r="6.5" />
                <path d="m16 16 4 4" />
              </svg>
              {nav.searchCorpus}
            </Link>
            <button
              type="button"
              onClick={() => setMenuOpen((value) => !value)}
              aria-label={nav.toggleMenu}
              aria-expanded={menuOpen}
              aria-controls="mobile-navigation"
              className="grid h-10 w-10 place-items-center rounded-md border border-border bg-surface text-foreground transition-colors hover:border-accent hover:text-accent sm:h-11 sm:w-11 lg:hidden"
            >
              <span className="relative h-4 w-5" aria-hidden>
                <motion.span transition={{ duration: reduce ? 0 : 0.18 }} animate={menuOpen ? { rotate: 45, y: 6 } : { rotate: 0, y: 0 }} className="absolute left-0 top-0 h-px w-5 bg-current" />
                <motion.span transition={{ duration: reduce ? 0 : 0.18 }} animate={menuOpen ? { opacity: 0 } : { opacity: 1 }} className="absolute left-0 top-[7px] h-px w-5 bg-current" />
                <motion.span transition={{ duration: reduce ? 0 : 0.18 }} animate={menuOpen ? { rotate: -45, y: -7 } : { rotate: 0, y: 0 }} className="absolute left-0 top-[14px] h-px w-5 bg-current" />
              </span>
            </button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {menuOpen ? (
          <motion.div
            key="mobile-navigation-layer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.18 }}
            className="fixed inset-x-0 bottom-0 top-16 z-40 sm:top-[4.5rem] lg:hidden"
          >
            <button type="button" aria-label="Close navigation menu" onClick={() => setMenuOpen(false)} className="absolute inset-0 bg-foreground/10 backdrop-blur-[1px]" />
            <motion.div
              id="mobile-navigation"
              initial={reduce ? undefined : { y: -10 }}
              animate={{ y: 0 }}
              exit={reduce ? undefined : { y: -10 }}
              transition={{ duration: reduce ? 0 : 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="relative border-b border-border bg-background px-4 py-3 shadow-[0_6px_8px_-6px_var(--shadow-color)]"
            >
              <nav className="mx-auto flex max-w-7xl flex-col" aria-label={nav.mobileNav}>
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMenuOpen(false)}
                    aria-current={isActive(link.href) ? "page" : undefined}
                    className={`group flex min-h-16 items-center justify-between gap-5 border-b border-border px-1 py-3 ${
                      isActive(link.href) ? "text-accent" : "text-foreground"
                    }`}
                  >
                    <span>
                      <span className="block text-base font-semibold">{link.label}</span>
                      <span className="mt-1 block text-xs font-medium text-muted">{link.detail}</span>
                    </span>
                    <span aria-hidden className="text-muted transition-transform duration-200 group-hover:translate-x-1 rtl:-scale-x-100 rtl:group-hover:-translate-x-1">→</span>
                  </Link>
                ))}
                <Link href="/about" onClick={() => setMenuOpen(false)} className="flex min-h-14 items-center px-1 text-sm font-semibold text-foreground">{nav.aboutProject}</Link>
              </nav>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
