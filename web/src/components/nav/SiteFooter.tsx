import Link from "next/link";
import { amiri } from "@/lib/fonts";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-border bg-surface/60">
      <div className="mx-auto grid max-w-5xl gap-10 px-4 py-12 sm:grid-cols-3 sm:px-6">
        <div>
          <p className="font-serif text-xl">
            usul<span className="text-accent">16</span>
          </p>
          <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-muted`}>
            مكتبة الحديث الشيعي
          </p>
          <p className="mt-3 max-w-xs text-sm text-muted">
            An open library of Shia hadith — the text, the chain, and the footnotes, cited to the printed page.
          </p>
        </div>

        <nav className="text-sm">
          <p className="font-semibold tracking-wide text-muted uppercase">Explore</p>
          <ul className="mt-3 space-y-2">
            <li>
              <Link href="/books" className="text-foreground/80 transition hover:text-accent">
                The Books
              </Link>
            </li>
            <li>
              <Link href="/search" className="text-foreground/80 transition hover:text-accent">
                Search
              </Link>
            </li>
            <li>
              <Link href="/about" className="text-foreground/80 transition hover:text-accent">
                About the project
              </Link>
            </li>
          </ul>
        </nav>

        <div className="text-sm">
          <p className="font-semibold tracking-wide text-muted uppercase">The corpus</p>
          <p className="mt-3 max-w-xs text-muted">
            Texts are sourced from the eShia digital library and presented with their original pagination, so
            every citation can be checked against the printed edition.
          </p>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-muted sm:px-6">
          <p>© {new Date().getFullYear()} Usul16</p>
          <p>Free to read. No account, no login.</p>
        </div>
      </div>
    </footer>
  );
}
