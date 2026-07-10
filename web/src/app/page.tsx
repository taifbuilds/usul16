import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { getStats } from "@/lib/api/stats";
import type { BookSummary, LibraryStats } from "@/lib/api/types";
import { SearchBox } from "@/components/nav/SearchBox";
import { BookCard } from "@/components/books/BookCard";
import { Reveal } from "@/components/ui/Reveal";
import { CountUp } from "@/components/ui/CountUp";
import { HeroOrnament } from "@/components/home/HeroOrnament";
import { amiri } from "@/lib/fonts";

// This app's content comes from a local backend that may not be running at
// build time (and changes as crawls progress) — always render at request
// time rather than attempting to statically prerender against a live API.
export const dynamic = "force-dynamic";

const TRY_SEARCHES = ["العقل", "الصلاة", "التوحيد", "الصوم"];

const FEATURES = [
  {
    title: "The original text",
    body: "Every page in the Arabic of the printed critical edition, set in a typeface made for it — nothing paraphrased, nothing abridged.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <path d="M12 5.5C10 4 7.5 3.5 4 3.5v15c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2v-15c-3.5 0-6 .5-8 2Z" />
        <path d="M12 5.5v15" />
      </svg>
    ),
  },
  {
    title: "Chain and matn, apart",
    body: "The chain of transmission is set off from the report itself, and hadith are numbered as in the edition — the page reads the way scholars cite it.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <path d="M9.5 14.5l5-5" />
        <path d="M8.5 11l-3 3a3 3 0 104.24 4.24l3-3" />
        <path d="M15.5 13l3-3a3 3 0 10-4.24-4.24l-3 3" />
      </svg>
    ),
  },
  {
    title: "Cited to the page",
    body: "Book, volume, page — one click copies a citation you can hand to anyone, and every page links back to its printed source.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <path d="M10 8H6a1 1 0 00-1 1v3a1 1 0 001 1h2.5c0 2-1 3.5-3.5 4" />
        <path d="M19 8h-4a1 1 0 00-1 1v3a1 1 0 001 1h2.5c0 2-1 3.5-3.5 4" />
      </svg>
    ),
  },
];

async function loadHomeData(): Promise<{ featured: BookSummary[]; stats: LibraryStats | null }> {
  // The home page should still render (hero, features, footer) even when the
  // backend is down — degrade to an empty shelf instead of a 500.
  const [featured, stats] = await Promise.all([
    getBooks({ limit: 4, hasContent: true }).catch(() => [] as BookSummary[]),
    getStats().catch(() => null),
  ]);
  return { featured, stats };
}

export default async function HomePage() {
  const { featured, stats } = await loadHomeData();

  return (
    <div>
      {/* ---------------------------------------------------------- hero */}
      <section className="relative overflow-hidden border-b border-border">
        <HeroOrnament />

        <div className="relative mx-auto max-w-3xl px-4 pt-24 pb-20 text-center sm:px-6 sm:pt-32 sm:pb-28">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/90 px-4 py-1.5 text-xs font-medium tracking-[0.18em] text-muted uppercase shadow-sm">
              <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-accent" />A living library of Shia
              hadith
            </span>
          </div>

          <h1 className="animate-fade-up anim-delay-1 mt-8 font-serif text-5xl leading-[1.08] tracking-tight sm:text-6xl">
            The whole tradition,
            <br />
            <span className="text-gold italic">in one quiet room.</span>
          </h1>

          <p
            dir="rtl"
            lang="ar"
            className={`${amiri.className} animate-fade-up anim-delay-2 mt-6 text-xl text-muted`}
          >
            مكتبة الحديث الشيعي — النص، والسند، والهوامش
          </p>

          <p className="animate-fade-up anim-delay-3 mx-auto mt-5 max-w-xl text-lg text-foreground/70">
            Read and search the hadith of the Prophet and the Ahl al-Bayt — the Four Books and centuries of
            collections, in their original Arabic.
          </p>

          <div className="animate-fade-up anim-delay-4 mx-auto mt-9 max-w-xl">
            <div className="rounded-full shadow-lg shadow-accent/5">
              <SearchBox size="lg" />
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-sm">
              <span className="text-muted">Try:</span>
              {TRY_SEARCHES.map((term) => (
                <Link
                  key={term}
                  href={`/search?q=${encodeURIComponent(term)}`}
                  dir="rtl"
                  lang="ar"
                  className={`${amiri.className} rounded-full border border-border bg-surface px-3.5 py-1 text-base text-foreground/75 transition hover:border-accent hover:text-accent`}
                >
                  {term}
                </Link>
              ))}
            </div>
          </div>

          <div className="animate-fade-up anim-delay-5 mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/books"
              className="rounded-full bg-foreground px-7 py-3 font-medium text-background shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
            >
              Start reading →
            </Link>
            <Link
              href="/about"
              className="rounded-full border border-border bg-surface px-7 py-3 font-medium text-foreground/80 transition hover:border-accent hover:text-accent"
            >
              About the project
            </Link>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------- stats */}
      {stats ? (
        <section className="border-b border-border bg-surface/60">
          <div className="mx-auto grid max-w-5xl grid-cols-3 gap-6 px-4 py-12 text-center sm:px-6">
            <Reveal>
              <p className="font-serif text-4xl text-foreground sm:text-5xl">
                <CountUp value={stats.pages_digitized} />
              </p>
              <p className="mt-2 text-xs font-semibold tracking-[0.18em] text-muted uppercase">Pages digitized</p>
            </Reveal>
            <Reveal delay={120}>
              <p className="font-serif text-4xl text-foreground sm:text-5xl">
                <CountUp value={stats.books_readable} />
              </p>
              <p className="mt-2 text-xs font-semibold tracking-[0.18em] text-muted uppercase">Books readable</p>
            </Reveal>
            <Reveal delay={240}>
              <p className="font-serif text-4xl text-foreground sm:text-5xl">
                <CountUp value={stats.authors} />
              </p>
              <p className="mt-2 text-xs font-semibold tracking-[0.18em] text-muted uppercase">Authors indexed</p>
            </Reveal>
          </div>
        </section>
      ) : null}

      {/* ------------------------------------------------------ features */}
      <section className="mx-auto max-w-5xl px-4 py-20 sm:px-6">
        <Reveal>
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-accent uppercase">The reading room</p>
              <h2 className="mt-2 font-serif text-3xl sm:text-4xl">Built for how hadith are read.</h2>
            </div>
            <p dir="rtl" lang="ar" className={`${amiri.className} hidden text-3xl text-gold sm:block`}>
              القراءة
            </p>
          </div>
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {FEATURES.map((feature, index) => (
            <Reveal key={feature.title} delay={index * 120}>
              <div className="group h-full rounded-2xl border border-border bg-surface p-6 transition hover:-translate-y-1 hover:border-accent hover:shadow-md">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-badge-verified text-accent transition group-hover:bg-accent group-hover:text-accent-foreground">
                  {feature.icon}
                </div>
                <h3 className="mt-5 font-serif text-xl">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{feature.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------ featured */}
      {featured.length > 0 ? (
        <section className="border-t border-border bg-surface/40">
          <div className="mx-auto max-w-5xl px-4 py-20 sm:px-6">
            <Reveal>
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold tracking-[0.18em] text-accent uppercase">On the shelf</p>
                  <h2 className="mt-2 font-serif text-3xl sm:text-4xl">Available to read now.</h2>
                </div>
                <Link
                  href="/books"
                  className="hidden shrink-0 text-sm font-medium text-accent hover:underline sm:block"
                >
                  Browse all →
                </Link>
              </div>
            </Reveal>

            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {featured.map((book, index) => (
                <Reveal key={book.id} delay={index * 100}>
                  <BookCard book={book} index={index + 1} />
                </Reveal>
              ))}
            </div>

            <div className="mt-8 text-center sm:hidden">
              <Link href="/books" className="text-sm font-medium text-accent hover:underline">
                Browse all →
              </Link>
            </div>
          </div>
        </section>
      ) : null}

      {/* ----------------------------------------------------------- cta */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-3xl px-4 py-20 text-center sm:px-6">
          <Reveal>
            <p dir="rtl" lang="ar" className={`${amiri.className} text-2xl text-gold`}>
              اقرأ
            </p>
            <h2 className="mt-4 font-serif text-3xl leading-snug sm:text-4xl">
              Open a book. The tradition is
              <br className="hidden sm:block" /> already waiting.
            </h2>
            <Link
              href="/books"
              className="mt-8 inline-block rounded-full bg-accent px-8 py-3.5 font-medium text-accent-foreground shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
            >
              Browse the library →
            </Link>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
