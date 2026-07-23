import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { getStats } from "@/lib/api/stats";
import type { BookSummary, LibraryStats } from "@/lib/api/types";
import { BookCard } from "@/components/books/BookCard";
import { Hero } from "@/components/home/Hero";
import { amiri } from "@/lib/fonts";

export const dynamic = "force-dynamic";

const RESEARCH_PATHS = [
  {
    href: "/books",
    title: "Read",
    subtitle: "Read a collection in order, by chapter or by the pages of the printed edition.",
    action: "Open the library",
    icon: "book",
  },
  {
    href: "/search",
    title: "Find",
    subtitle: "Search the Arabic and English together and open the matching report.",
    action: "Search the collections",
    icon: "search",
  },
  {
    href: "/graph",
    title: "Investigate",
    subtitle: "Open any narrator to see who they narrated from and who narrated from them.",
    action: "Browse the narrators",
    icon: "network",
  },
] as const;

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

function PathIcon({ name }: { name: (typeof RESEARCH_PATHS)[number]["icon"] }) {
  if (name === "search") {
    return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>;
  }
  if (name === "network") {
    return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="6" r="2.5" /><circle cx="18" cy="18" r="2.5" /><path d="m8.3 10.9 7.4-3.8M8.3 13.1l7.4 3.8" /></svg>;
  }
  return <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16ZM20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" /></svg>;
}

export default async function HomePage() {
  const { featured, stats } = await loadHomeData();

  return (
    <div>
      <Hero />

      {stats ? (
        <section className="border-b border-border bg-surface" aria-label="Corpus coverage">
          <div className="mx-auto grid max-w-[90rem] grid-cols-2 px-4 sm:px-6 lg:grid-cols-[1.35fr_repeat(4,1fr)] lg:px-8">
            <div className="col-span-2 flex items-center border-b border-border py-5 lg:col-span-1 lg:border-b-0 lg:pr-8">
              <p className="max-w-xs text-sm font-semibold leading-6 text-foreground">The library as it currently stands.</p>
            </div>
            {[
              [stats.books_readable, "Readable books"],
              [stats.pages_digitized, "Digitised pages"],
              [stats.books_catalogued, "Catalogued works"],
              [stats.authors, "Indexed authors"],
            ].map(([value, label]) => (
              <div key={label} className="border-l border-border px-4 py-5 sm:px-6">
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
            <p className="text-sm font-semibold text-accent">Using the library</p>
            <h2 className="mt-3 max-w-xl font-serif text-4xl font-semibold leading-tight sm:text-5xl">Read, search, and trace narrators.</h2>
          </div>
          <p className="max-w-2xl text-base leading-8 text-muted lg:justify-self-end">
            Read a collection in full, look up a specific narration, or follow a narrator across the tradition. Each report stays linked to its source.
          </p>
        </div>

        <div className="mt-10 border-y border-border lg:grid lg:grid-cols-3">
          {RESEARCH_PATHS.map((path, index) => (
            <Link key={path.href} href={path.href} className={`research-path group ${index ? "border-t border-border lg:border-l lg:border-t-0" : ""}`}>
              <span className="research-path__icon"><PathIcon name={path.icon} /></span>
              <span className="min-w-0 flex-1">
                <span className="font-serif text-2xl font-semibold text-foreground">{path.title}</span>
                <span className="mt-2 block max-w-sm text-sm leading-6 text-muted">{path.subtitle}</span>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-accent">
                  {path.action}<span aria-hidden className="transition-transform duration-200 group-hover:translate-x-1">→</span>
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
                <p className="text-sm font-semibold text-[color:var(--stage-accent)]">The collections</p>
                <h2 className="mt-2 font-serif text-4xl font-semibold text-[color:var(--stage-ink)] sm:text-5xl">The Four Books and later works.</h2>
              </div>
              <Link href="/books" className="inline-flex items-center gap-2 text-sm font-semibold text-[color:var(--stage-accent)] hover:underline">
                View the full catalogue <span aria-hidden>→</span>
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
          <p dir="rtl" lang="ar" className={`${amiri.className} text-3xl text-gold`}>من النص إلى الدليل</p>
          <h2 className="mt-4 max-w-xl font-serif text-4xl font-semibold leading-tight sm:text-5xl">What each record contains.</h2>
          <p className="mt-5 max-w-xl text-base leading-8 text-muted">
            Every hadith record brings together the Arabic text, its translation, the narrators in its chain, the wider transmission, and a citation back to the printed edition.
          </p>
        </div>

        <ol className="evidence-sequence">
          {[
            ["Arabic text", "The narration as printed, with the chain, body, chapter headings, and footnotes kept distinct."],
            ["English translation", "The English alongside the Arabic, with the translator and source named on each one."],
            ["Narrator profiles", "Each name in the chain links to that narrator, with the evidence for the identification."],
            ["Transmission", "How the narrators connect across the collections, linked back to the reports that establish each link."],
            ["Citation", "A stable reference, checkable against the volume, page, and original scan."],
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
            <p className="font-serif text-2xl font-semibold sm:text-3xl">Open access.</p>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted">No account required. The full library is free to read, search, and cite.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/about" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">About the project</Link>
            <Link href="/books" className="inline-flex h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground hover:bg-accent-strong">Start reading</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
