import type { Metadata } from "next";
import Link from "next/link";

import { getCorpusStatus } from "@/lib/api/books";
import { COLLECTION_NAMES, corpusMaturity } from "@/lib/corpus-maturity";

export const metadata: Metadata = {
  title: "Corpus status and methodology",
  description: "Current Usul16 corpus coverage, review maturity, translation coverage, and research limitations.",
};

export const dynamic = "force-dynamic";

function number(value: number): string {
  return new Intl.NumberFormat("en-GB").format(value);
}

function percentage(part: number, whole: number): string {
  if (!whole) return "—";
  return `${((part / whole) * 100).toFixed(1)}%`;
}

export default async function MethodologyPage() {
  const { books } = await getCorpusStatus();

  return (
    <div className="mx-auto max-w-[90rem] px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
      <header className="grid gap-8 border-b border-border pb-12 lg:grid-cols-[1fr_0.72fr] lg:items-end">
        <div>
          <p className="text-sm font-semibold text-accent">Research transparency</p>
          <h1 className="mt-4 max-w-4xl font-serif text-5xl font-semibold leading-[1.05] tracking-[-0.025em] sm:text-6xl">
            What is ready, what is provisional, and how to verify it.
          </h1>
        </div>
        <p className="max-w-xl text-lg leading-8 text-muted">
          Different collections are at different stages of editing. Every number on this page is read live from the database, so you can see exactly where each one stands.
        </p>
      </header>

      <section aria-labelledby="corpus-heading" className="py-14">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="corpus-heading" className="font-serif text-3xl font-semibold">Where each collection stands</h2>
            <p className="mt-2 max-w-3xl leading-7 text-muted">A book you can read isn&rsquo;t always one we&rsquo;ve checked line by line yet—this table shows the difference.</p>
          </div>
          <p className="text-sm text-muted">Live database counts</p>
        </div>

        <div className="mt-8 overflow-x-auto border-y border-border">
          <table className="w-full min-w-[58rem] border-collapse text-left text-sm">
            <thead className="text-muted">
              <tr className="border-b border-border">
                <th scope="col" className="py-4 pr-6 font-semibold">Collection and state</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Pages</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Hadiths</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Parsed chains</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Chains flagged</th>
                <th scope="col" className="pl-4 py-4 text-right font-semibold">Public English</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {books.map((book) => {
                const maturity = corpusMaturity(book.source_book_id);
                return (
                  <tr key={book.source_book_id}>
                    <th scope="row" className="py-5 pr-6 font-normal">
                      <Link href={`/books/${book.book_id}`} className="font-semibold text-foreground hover:text-accent hover:underline">
                        {COLLECTION_NAMES[book.source_book_id] ?? book.title_original}
                      </Link>
                      <span className="mt-1 block text-xs font-semibold text-accent">{maturity?.label}</span>
                      <span className="mt-1 block max-w-md text-xs leading-5 text-muted">{maturity?.summary}</span>
                    </th>
                    <td className="px-4 py-5 text-right tabular-nums">{number(book.pages_digitized)}</td>
                    <td className="px-4 py-5 text-right tabular-nums">{number(book.visible_hadiths)}</td>
                    <td className="px-4 py-5 text-right tabular-nums">{number(book.parsed_chains)}</td>
                    <td className="px-4 py-5 text-right tabular-nums">{number(book.chains_needing_review)}</td>
                    <td className="pl-4 py-5 text-right tabular-nums">
                      {number(book.public_english_translations)}
                      {book.visible_hadiths ? <span className="ml-2 text-xs text-muted">{percentage(book.public_english_translations, book.visible_hadiths)}</span> : null}
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
          <h2 className="font-serif text-2xl font-semibold">Counting Al-Kafi</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            Usul16 currently exposes 15,335 Al-Kafi records from the represented edition. The often-cited total of 16,199 follows a different counting tradition. Differences can arise from edition boundaries, reports combined or separated, headings, repetitions, and rejected parser artefacts; the totals must not be treated as interchangeable.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-2xl font-semibold">Editorial model</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            Source Arabic and printed pagination remain authoritative. Hadith boundaries, chain tokenisation, narrator resolution and translations are layered research data. Automated results retain review states and supporting evidence so they can be challenged and revised.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-2xl font-semibold">How to cite responsibly</h2>
          <p className="mt-4 leading-7 text-foreground/85">
            Cite the printed work, volume and page first, then include the stable Usul16 identifier and permanent URL. Translation and narrator conclusions should be described as research aids unless their review state says otherwise.
          </p>
        </section>
      </div>
    </div>
  );
}
