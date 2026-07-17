import Link from "next/link";
import { getStats } from "@/lib/api/stats";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "About",
  description: "Why Usul16 exists and how it approaches source verification, translation, narrator identity, and scholarly judgement.",
  alternates: { canonical: "/about" },
};

export default async function AboutPage() {
  const stats = await getStats();
  const figures = [
    [stats.pages_digitized, "Digitised pages"],
    [stats.books_readable, "Readable books"],
    [stats.authors, "Indexed authors"],
  ] as const;

  return (
    <div className="mx-auto max-w-[90rem] px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
      <header className="grid gap-10 border-b border-border pb-12 lg:grid-cols-[1fr_0.75fr] lg:items-end">
        <div>
          <p className="text-sm font-semibold text-accent">About Usul16</p>
          <h1 className="mt-4 max-w-4xl font-serif text-5xl font-semibold leading-[1.05] tracking-[-0.025em] sm:text-6xl">A hadith library built to withstand serious questions.</h1>
        </div>
        <p className="max-w-xl text-lg leading-8 text-muted">
          Usul16 brings reading, discovery, citation, narrator identity, and transmission evidence into one source-verifiable environment.
        </p>
      </header>

      <div className="grid gap-14 py-14 lg:grid-cols-[0.72fr_1.28fr]">
        <aside>
          <p className="text-sm font-semibold text-foreground">Current corpus</p>
          <dl className="mt-4 divide-y divide-border border-y border-border">
            {figures.map(([value, label]) => (
              <div key={label} className="flex items-baseline justify-between gap-5 py-4">
                <dt className="text-sm text-muted">{label}</dt>
                <dd className="font-serif text-2xl font-semibold tabular-nums">{value.toLocaleString()}</dd>
              </div>
            ))}
          </dl>
        </aside>

        <div className="max-w-3xl space-y-10">
          <section>
            <h2 className="font-serif text-3xl font-semibold">Why it exists</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>The Shia hadith corpus runs across tens of thousands of narrations in the Four Books and centuries of later collections. Too much of it remains fragmented across dense scans, ageing websites, isolated translations, and databases that hide how a result relates to the printed source.</p>
              <p>Usul16 is an attempt to keep the corpus connected: Arabic to translation, hadith to chain, narrator mention to resolved identity, transmission edge to its supporting narrations, and every record back to volume and page.</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">What authority means here</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>The Arabic text and the cited printed edition remain authoritative. English translations are reading aids, and narrator resolutions are research conclusions whose evidence and review state should be inspectable.</p>
              <p>Usul16 does not replace scholarly judgement. It makes the underlying material easier to find, verify, compare, and cite—so judgement can begin from stronger evidence.</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">The ambition</h2>
            <p className="mt-4 text-base leading-8 text-foreground/85">The Four Books are the proving ground for a repeatable corpus, translation, and rijāl system. Once that standard is dependable, the same architecture can extend through Biḥār al-Anwār and the wider tradition without lowering the bar for provenance or review.</p>
          </section>

          <div className="flex flex-wrap gap-3 border-t border-border pt-9">
            <Link href="/books" className="inline-flex h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground hover:bg-accent-strong">Open the library</Link>
            <Link href="/graph" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">Inspect the network</Link>
            <Link href="/methodology" className="inline-flex h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">Review corpus status</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
