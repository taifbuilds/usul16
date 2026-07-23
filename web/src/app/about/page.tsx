import Link from "next/link";
import { getStats } from "@/lib/api/stats";
import type { Metadata } from "next";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { getLocale } from "@/lib/i18n/locale";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const t = getDictionary(await getLocale());
  return {
    title: t.about.metaTitle,
    description: t.about.lead,
    alternates: { canonical: "/about" },
  };
}

export default async function AboutPage() {
  const [stats, locale] = await Promise.all([getStats(), getLocale()]);
  const t = getDictionary(locale);
  const numberLocale = locale === "ar" ? "ar-EG" : "en-GB";
  const figures = [
    [stats.pages_digitized, t.about.digitisedPages],
    [stats.books_readable, t.about.readableBooks],
    [stats.authors, t.about.indexedAuthors],
  ] as const;

  return (
    <div className="mx-auto max-w-[90rem] px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
      <header className="grid gap-10 border-b border-border pb-12 lg:grid-cols-[1fr_0.75fr] lg:items-end">
        <div>
          <p className="text-sm font-semibold text-accent">{t.about.eyebrow}</p>
          <h1 className="mt-4 max-w-4xl font-serif text-5xl font-semibold leading-[1.05] tracking-[-0.025em] sm:text-6xl">{t.about.title}</h1>
        </div>
        <p className="max-w-xl text-lg leading-8 text-muted">
          {t.about.lead}
        </p>
      </header>

      <div className="grid gap-14 py-14 lg:grid-cols-[0.72fr_1.28fr]">
        <aside>
          <p className="text-sm font-semibold text-foreground">{t.about.currentCorpus}</p>
          <dl className="mt-4 divide-y divide-border border-y border-border">
            {figures.map(([value, label]) => (
              <div key={label} className="flex items-baseline justify-between gap-5 py-4">
                <dt className="text-sm text-muted">{label}</dt>
                <dd className="font-serif text-2xl font-semibold tabular-nums">{value.toLocaleString(numberLocale)}</dd>
              </div>
            ))}
          </dl>
        </aside>

        <div className="max-w-3xl space-y-10">
          <section>
            <h2 className="font-serif text-3xl font-semibold">{t.about.whatHeading}</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>{t.about.whatBody1}</p>
              <p>{t.about.whatBody2}</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">{t.about.readingHeading}</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>{t.about.readingBody1}</p>
              <p>{t.about.readingBody2}</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">{t.about.goingHeading}</h2>
            <p className="mt-4 text-base leading-8 text-foreground/85">{t.about.goingBody}</p>
          </section>

          <div className="flex flex-wrap gap-3 border-t border-border pt-9">
            <Link href="/books" className="inline-flex h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground hover:bg-accent-strong">{t.about.openLibrary}</Link>
            <Link href="/graph" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">{t.about.inspectNetwork}</Link>
            <Link href="/methodology" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">{t.about.reviewStatus}</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
