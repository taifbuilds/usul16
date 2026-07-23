"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useState } from "react";
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

  return (
    <>
      <a href="#main-content" className="skip-link">{nav.skip}</a>
      <header className="sticky top-0 z-50 border-b border-border bg-background/96 backdrop-blur-sm">
        <div className="mx-auto flex h-[4.5rem] max-w-[90rem] items-center gap-5 px-4 sm:px-6 lg:px-8">
          <Link href="/" className="group flex items-center gap-3 whitespace-nowrap" aria-label="Usul16 home">
            <span className="brand-mark" aria-hidden>
              <span className={`${amiri.className} text-base leading-none`}>١٦</span>
            </span>
            <span className="flex flex-col leading-none">
              <span className="font-serif text-xl font-semibold tracking-[-0.015em] text-foreground">Usul16</span>
              <span className="mt-1 text-xs font-semibold text-muted">{nav.brandSub}</span>
            </span>
          </Link>

          <nav className="ms-3 hidden h-full items-stretch lg:flex" aria-label={nav.primaryNav}>
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
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

          <div className="ms-auto flex items-center gap-2">
            <Link
              href="/about"
              className={`hidden min-h-11 items-center px-3 text-sm font-medium transition-colors sm:inline-flex ${
                isActive("/about") ? "text-accent" : "text-muted hover:text-foreground"
              }`}
            >
              {nav.about}
            </Link>
            <LanguageToggle locale={locale} />
            <ThemeToggle />
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
              className="grid h-11 w-11 place-items-center rounded-md border border-border bg-surface text-foreground lg:hidden"
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
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: reduce ? 0 : 0.18 }}
            className="fixed inset-x-0 top-[4.5rem] z-40 border-b border-border bg-background px-4 py-5 shadow-[0_6px_8px_-6px_var(--shadow-color)] lg:hidden"
          >
            <nav className="mx-auto flex max-w-7xl flex-col" aria-label={nav.mobileNav}>
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center justify-between border-b border-border py-4 text-base font-semibold ${
                    isActive(link.href) ? "text-accent" : "text-foreground"
                  }`}
                >
                  <span>{link.label}</span>
                  <span className="text-xs font-medium text-muted">{link.detail}</span>
                </Link>
              ))}
              <Link href="/about" onClick={() => setMenuOpen(false)} className="py-4 text-base font-semibold text-foreground">{nav.aboutProject}</Link>
            </nav>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
