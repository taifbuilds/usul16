import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { getStats } from "@/lib/api/stats";
import type { BookSummary, LibraryStats } from "@/lib/api/types";
import { BookCard } from "@/components/books/BookCard";
import { Hero } from "@/components/home/Hero";
import { amiri } from "@/lib/fonts";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { getLocale } from "@/lib/i18n/locale";

export const dynamic = "force-dynamic";

async function loadHomeData(): Promise<{ featured: BookSummary[]; stats: LibraryStats | null }> {
  const [books, stats] = await Promise.all([
    getBooks({ limit: 50, hasContent: true }).catch(() => [] as BookSummary[]),
    getStats().catch(() => null),
  ]);
  const fourBooks = ["11005", "11021", "10083", "11002"];
  const featured = fourBooks
    .map((sourceId) => books.find((book) => book.source_book_id === sourceId))
    .filter((book): book is BookSummary => Boolean(book));
  for (const book of books) {
    if (featured.length >= 4) break;
    if (!featured.some((item) => item.id === book.id)) featured.push(book);
  }
  return { featured, stats };
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-GB").format(value);
}

function PathIcon({ name }: { name: "book" | "search" | "network" }) {
  if (name === "search") {
    return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>;
  }
  if (name === "network") {
    return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="6" r="2.5" /><circle cx="18" cy="18" r="2.5" /><path d="m8.3 10.9 7.4-3.8M8.3 13.1l7.4 3.8" /></svg>;
  }
  return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16ZM20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" /></svg>;
}

export default async function HomePage() {
  const [{ featured, stats }, t] = await Promise.all([
    loadHomeData(),
    getLocale().then(getDictionary),
  ]);
  const researchPaths = [
    { href: "/books", title: t.nav.read, subtitle: t.paths.readBody, action: t.paths.readAction, icon: "book" as const },
    { href: "/search", title: t.nav.find, subtitle: t.paths.findBody, action: t.paths.findAction, icon: "search" as const },
    { href: "/graph", title: t.nav.investigate, subtitle: t.paths.investigateBody, action: t.paths.investigateAction, icon: "network" as const },
  ];

  return (
    <div>
      <Hero hero={t.hero} search={t.search} />

      {stats ? (
        <section className="border-b border-border bg-surface" aria-label={t.stats.coverageLabel}>
          <div className="mx-auto grid max-w-[90rem] grid-cols-2 px-4 sm:px-6 lg:grid-cols-[1.35fr_repeat(4,1fr)] lg:px-8">
            <div className="col-span-2 flex items-center border-b border-border py-5 lg:col-span-1 lg:border-b-0 lg:pe-8">
              <p className="max-w-xs text-sm font-semibold leading-6 text-foreground">{t.stats.intro}</p>
            </div>
            {[
              [stats.books_readable, t.stats.readableBooks],
              [stats.pages_digitized, t.stats.digitisedPages],
              [stats.books_catalogued, t.stats.cataloguedWorks],
              [stats.authors, t.stats.indexedAuthors],
            ].map(([value, label]) => (
              <div key={label} className="border-s border-border px-4 py-5 sm:px-6">
                <p className="font-serif text-2xl font-semibold tabular-nums text-foreground">{formatNumber(Number(value))}</p>
                <p className="mt-1 text-xs font-medium text-muted">{label}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mx-auto max-w-[90rem] px-4 py-18 sm:px-6 sm:py-22 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.75fr_1.25fr] lg:items-end">
          <div>
            <p className="text-sm font-semibold text-accent">{t.paths.eyebrow}</p>
            <h2 className="mt-3 max-w-xl font-serif text-4xl font-semibold leading-tight sm:text-5xl">{t.paths.title}</h2>
          </div>
          <p className="max-w-2xl text-base leading-8 text-muted lg:justify-self-end">
            {t.paths.intro}
          </p>
        </div>

        <div className="mt-10 border-y border-border lg:grid lg:grid-cols-3">
          {researchPaths.map((path, index) => (
            <Link key={path.href} href={path.href} className={`research-path group ${index ? "border-t border-border lg:border-s lg:border-t-0" : ""}`}>
              <span className="research-path__icon"><PathIcon name={path.icon} /></span>
              <span className="min-w-0 flex-1">
                <span className="font-serif text-2xl font-semibold text-foreground">{path.title}</span>
                <span className="mt-2 block max-w-sm text-sm leading-6 text-muted">{path.subtitle}</span>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-accent">
                  {path.action}<span aria-hidden className="transition-transform duration-200 group-hover:translate-x-1 rtl:-scale-x-100 rtl:group-hover:-translate-x-1">→</span>
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {featured.length > 0 ? (
        <section className="library-stage border-y border-border">
          <div className="mx-auto max-w-[90rem] px-4 py-18 sm:px-6 sm:py-22 lg:px-8">
            <div className="flex flex-wrap items-end justify-between gap-6">
              <div>
                <p className="text-sm font-semibold text-[color:var(--stage-accent)]">{t.collections.eyebrow}</p>
                <h2 className="mt-2 font-serif text-4xl font-semibold text-[color:var(--stage-ink)] sm:text-5xl">{t.collections.title}</h2>
              </div>
              <Link href="/books" className="inline-flex items-center gap-2 text-sm font-semibold text-[color:var(--stage-accent)] hover:underline">
                {t.collections.viewAll} <span aria-hidden className="rtl:-scale-x-100">→</span>
              </Link>
            </div>

            <div className="mt-14 grid gap-x-6 gap-y-14 sm:grid-cols-2 lg:grid-cols-4">
              {featured.map((book, index) => <BookCard key={book.id} book={book} index={index + 1} />)}
            </div>
          </div>
        </section>
      ) : null}

      <section className="mx-auto grid max-w-[90rem] gap-12 px-4 py-20 sm:px-6 sm:py-24 lg:grid-cols-[0.85fr_1.15fr] lg:items-start lg:px-8">
        <div className="lg:sticky lg:top-28">
          <p dir="rtl" lang="ar" className={`${amiri.className} text-3xl text-gold`}>{t.evidence.arabic}</p>
          <h2 className="mt-4 max-w-xl font-serif text-4xl font-semibold leading-tight sm:text-5xl">{t.evidence.title}</h2>
          <p className="mt-5 max-w-xl text-base leading-8 text-muted">
            {t.evidence.intro}
          </p>
        </div>

        <ol className="evidence-sequence">
          {[
            [t.evidence.item1Title, t.evidence.item1Body],
            [t.evidence.item2Title, t.evidence.item2Body],
            [t.evidence.item3Title, t.evidence.item3Body],
            [t.evidence.item4Title, t.evidence.item4Body],
            [t.evidence.item5Title, t.evidence.item5Body],
          ].map(([title, body], index) => (
            <li key={title}>
              <span className="evidence-sequence__number">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3 className="font-serif text-2xl font-semibold">{title}</h3>
                <p className="mt-2 max-w-2xl text-sm leading-7 text-muted">{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-y border-border bg-surface">
        <div className="mx-auto grid max-w-[90rem] gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_auto] lg:items-center lg:px-8">
          <div>
            <p className="font-serif text-2xl font-semibold sm:text-3xl">{t.cta.title}</p>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted">{t.cta.body}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/about" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">{t.cta.about}</Link>
            <Link href="/books" className="inline-flex h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground hover:bg-accent-strong">{t.cta.start}</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
