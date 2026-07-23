import type { Metadata } from "next";
import Link from "next/link";

import { getCorpusStatus } from "@/lib/api/books";
import { COLLECTION_NAMES, corpusMaturity } from "@/lib/corpus-maturity";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { getLocale } from "@/lib/i18n/locale";

export async function generateMetadata(): Promise<Metadata> {
  const t = getDictionary(await getLocale());
  return { title: t.methodology.metaTitle, description: t.methodology.lead };
}

export const dynamic = "force-dynamic";

function percentage(part: number, whole: number): string {
  if (!whole) return "—";
  return `${((part / whole) * 100).toFixed(1)}%`;
}

export default async function MethodologyPage() {
  const [{ books }, locale] = await Promise.all([getCorpusStatus(), getLocale()]);
  const t = getDictionary(locale);
  const numberLocale = locale === "ar" ? "ar-EG" : "en-GB";
  const number = (value: number): string => new Intl.NumberFormat(numberLocale).format(value);

  return (
    <div className="mx-auto max-w-[90rem] px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
      <header className="grid gap-8 border-b border-border pb-12 lg:grid-cols-[1fr_0.72fr] lg:items-end">
        <div>
          <p className="text-sm font-semibold text-accent">{t.methodology.eyebrow}</p>
          <h1 className="mt-4 max-w-4xl font-serif text-5xl font-semibold leading-[1.05] tracking-[-0.025em] sm:text-6xl">
            {t.methodology.title}
          </h1>
        </div>
        <p className="max-w-xl text-lg leading-8 text-muted">
          {t.methodology.lead}
        </p>
      </header>

      <section aria-labelledby="corpus-heading" className="py-14">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="corpus-heading" className="font-serif text-3xl font-semibold">{t.methodology.corpusHeading}</h2>
            <p className="mt-2 max-w-3xl leading-7 text-muted">{t.methodology.corpusSub}</p>
          </div>
          <p className="text-sm text-muted">{t.methodology.liveCounts}</p>
        </div>

        <div className="mt-8 overflow-x-auto border-y border-border">
          <table className="w-full min-w-[58rem] border-collapse text-start text-sm">
            <thead className="text-muted">
              <tr className="border-b border-border">
                <th scope="col" className="py-4 pe-6 font-semibold">{t.methodology.colCollection}</th>
                <th scope="col" className="px-4 py-4 text-end font-semibold">{t.methodology.colPages}</th>
                <th scope="col" className="px-4 py-4 text-end font-semibold">{t.methodology.colHadiths}</th>
                <th scope="col" className="px-4 py-4 text-end font-semibold">{t.methodology.colChains}</th>
                <th scope="col" className="px-4 py-4 text-end font-semibold">{t.methodology.colFlagged}</th>
                <th scope="col" className="ps-4 py-4 text-end font-semibold">{t.methodology.colEnglish}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {books.map((book) => {
                const maturity = corpusMaturity(book.source_book_id);
                return (
                  <tr key={book.source_book_id}>
                    <th scope="row" className="py-5 pe-6 font-normal">
                      <Link href={`/books/${book.book_id}`} className="font-semibold text-foreground hover:text-accent hover:underline">
                        {COLLECTION_NAMES[book.source_book_id] ?? book.title_original}
                      </Link>
                      <span className="mt-1 block text-xs font-semibold text-accent">{maturity?.label}</span>
                      <span className="mt-1 block max-w-md text-xs leading-5 text-muted">{maturity?.summary}</span>
                    </th>
                    <td className="px-4 py-5 text-end tabular-nums">{number(book.pages_digitized)}</td>
                    <td className="px-4 py-5 text-end tabular-nums">{number(book.visible_hadiths)}</td>
                    <td className="px-4 py-5 text-end tabular-nums">{number(book.parsed_chains)}</td>
                    <td className="px-4 py-5 text-end tabular-nums">{number(book.chains_needing_review)}</td>
                    <td className="ps-4 py-5 text-end tabular-nums">
                      {number(book.public_english_translations)}
                      {book.visible_hadiths ? <span className="ms-2 text-xs text-muted">{percentage(book.public_english_translations, book.visible_hadiths)}</span> : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-12 border-t border-border py-14 lg:grid-cols-3">
        <section>
          <h2 className="font-serif text-2xl font-semibold">{t.methodology.countingHeading}</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            {t.methodology.countingBody}
          </p>
        </section>
        <section>
          <h2 className="font-serif text-2xl font-semibold">{t.methodology.editorialHeading}</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            {t.methodology.editorialBody}
          </p>
        </section>
        <section>
          <h2 className="font-serif text-2xl font-semibold">{t.methodology.citeHeading}</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            {t.methodology.citeBody}
          </p>
        </section>
      </div>
    </div>
  );
}
