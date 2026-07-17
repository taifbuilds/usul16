import Link from "next/link";
import { amiri } from "@/lib/fonts";

const PATHS = [
  { href: "/books", label: "Read the collections" },
  { href: "/search", label: "Search the corpus" },
  { href: "/graph", label: "Investigate transmissions" },
  { href: "/methodology", label: "Corpus status and methodology" },
];

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-border bg-background-2">
      <div className="mx-auto grid max-w-[90rem] gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[1.15fr_0.85fr_0.9fr] lg:px-8">
        <div>
          <div className="flex items-center gap-3">
            <span className="brand-mark brand-mark--quiet" aria-hidden><span className={`${amiri.className} text-base leading-none`}>١٦</span></span>
            <p className="font-serif text-xl font-semibold">Usul16</p>
          </div>
          <p dir="rtl" lang="ar" className={`${amiri.className} mt-5 text-2xl text-gold`}>أصول الحديث، موصولة بمصادرها</p>
          <p className="mt-4 max-w-md text-sm leading-7 text-muted">
            A living research library for Shia hadith—original Arabic, reading aids, parsed chains, narrator evidence, and citations back to the printed source.
          </p>
        </div>

        <nav aria-label="Research paths">
          <p className="text-sm font-semibold text-foreground">Research paths</p>
          <ul className="mt-4 divide-y divide-border border-y border-border text-sm">
            {PATHS.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="flex items-center justify-between py-3.5 text-muted transition-colors hover:text-accent">
                  {item.label}<span aria-hidden>→</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="text-sm">
          <p className="font-semibold text-foreground">Source policy</p>
          <p className="mt-4 leading-7 text-muted">
            The Arabic text and printed edition remain authoritative. Translations and identity resolutions are research aids whose provenance and review state should remain visible.
          </p>
          <Link href="/about" className="mt-4 inline-flex font-semibold text-accent hover:underline">About Usul16 →</Link>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-[90rem] flex-wrap justify-between gap-2 px-4 py-4 text-xs text-muted sm:px-6 lg:px-8">
          <p>&copy; {new Date().getFullYear()} Usul16</p>
          <p>No account required · Independent research project · Corpus status published</p>
        </div>
      </div>
    </footer>
  );
}
