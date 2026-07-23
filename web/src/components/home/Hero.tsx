import Link from "next/link";
import { SearchBox } from "@/components/nav/SearchBox";
import { amiri } from "@/lib/fonts";

const CHAIN = ["علي بن إبراهيم", "أبيه", "ابن أبي عمير", "أبي عبد الله عليه السلام"];

export function Hero() {
  return (
    <section className="home-hero border-b border-border">
      <div className="mx-auto grid max-w-[90rem] gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[minmax(0,1.05fr)_minmax(28rem,0.95fr)] lg:items-center lg:px-8 lg:py-24">
        <div className="max-w-3xl">
          <div className="mb-6 flex items-center gap-3 text-sm font-semibold text-accent">
            <span className="h-px w-9 bg-accent" aria-hidden />
            <span>Shia hadith library</span>
          </div>
          <h1 className="max-w-[15ch] font-serif text-[clamp(3rem,6vw,5.25rem)] font-semibold leading-[1.0] tracking-[-0.03em] text-foreground [text-wrap:balance]">
            The major Shia hadith collections, in Arabic and English.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-muted sm:text-xl sm:leading-9">
            The Four Books and later collections: the original Arabic with its English translation, the narrators in each chain linked to their profiles, and every report tied to the page it was printed on.
          </p>

          <div className="mt-9 max-w-2xl">
            <SearchBox size="lg" />
            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-medium text-muted">
              <span>Arabic and English</span>
              <span className="hidden h-1 w-1 rounded-full bg-border-strong sm:block" aria-hidden />
              <span>Free, no sign-up</span>
              <span className="hidden h-1 w-1 rounded-full bg-border-strong sm:block" aria-hidden />
              <span>Linked to the printed page</span>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/books" className="inline-flex h-11 items-center gap-2 rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground transition-[background-color,transform] hover:bg-accent-strong active:scale-[0.98]">
              Open the library
              <svg aria-hidden viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4">
                <path d="M4 10h12M12 6l4 4-4 4" />
              </svg>
            </Link>
            <Link href="/graph" className="inline-flex h-11 items-center rounded-md border border-border-strong bg-surface px-5 text-sm font-semibold text-foreground transition-[border-color,color,transform] hover:border-accent hover:text-accent active:scale-[0.98]">
              Narrator network
            </Link>
          </div>
        </div>

        <aside className="research-folio min-w-0" aria-label="Example source-linked hadith record">
          <div className="flex items-center justify-between gap-4 border-b border-[color:var(--folio-line)] px-5 py-4 sm:px-7">
            <div>
              <p className="text-xs font-semibold text-[color:var(--folio-muted)]">Research record</p>
              <p className="mt-1 font-mono text-xs font-semibold text-[color:var(--folio-accent)]">AK-1-42</p>
            </div>
            <p dir="rtl" lang="ar" className={`${amiri.className} text-2xl text-[color:var(--folio-ink)]`}>كتاب فضل العلم</p>
          </div>

          <div className="px-5 py-6 sm:px-7 sm:py-7">
            <p className="text-xs font-semibold text-[color:var(--folio-muted)]">Transmission chain</p>
            <ol dir="rtl" lang="ar" className={`${amiri.className} research-chain mt-4 flex flex-wrap items-center justify-end gap-2 text-base text-[color:var(--folio-ink)]`}>
              {CHAIN.map((name, index) => (
                <li key={name} className="research-chain__segment flex items-center gap-2">
                  <span className="research-chain__node rounded-full border border-[color:var(--folio-line)] bg-[color:var(--folio-chip)] px-3 py-1.5">{name}</span>
                  {index < CHAIN.length - 1 ? <span className="research-chain__arrow text-[color:var(--folio-accent)]" aria-hidden>←</span> : null}
                </li>
              ))}
            </ol>

            <div className="my-6 h-px bg-[color:var(--folio-line)]" />

            <blockquote dir="rtl" lang="ar" className={`${amiri.className} text-right text-3xl leading-[1.9] text-[color:var(--folio-ink)]`}>
              طَلَبُ الْعِلْمِ فَرِيضَةٌ عَلَى كُلِّ مُسْلِمٍ
            </blockquote>

            <div className="mt-6 grid grid-cols-[1fr_auto] items-end gap-5 border-t border-[color:var(--folio-line)] pt-5">
              <div>
                <p className="text-xs font-semibold text-[color:var(--folio-muted)]">Printed source</p>
                <p className="mt-1 text-sm font-semibold text-[color:var(--folio-ink)]">Al-Kāfī · vol. 1 · p. 30</p>
              </div>
              <span className="source-seal" aria-label="Source linked">
                <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4">
                  <path d="m7 12 3 3 7-7" />
                  <circle cx="12" cy="12" r="9" />
                </svg>
                Verified route
              </span>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
