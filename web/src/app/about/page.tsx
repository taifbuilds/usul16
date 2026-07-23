import Link from "next/link";
import { getStats } from "@/lib/api/stats";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "About",
  description: "What Usul16 is, how to read what you find, and where the project is going.",
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
          <h1 className="mt-4 max-w-4xl font-serif text-5xl font-semibold leading-[1.05] tracking-[-0.025em] sm:text-6xl">A source-linked library of Shia hadith.</h1>
        </div>
        <p className="max-w-xl text-lg leading-8 text-muted">
          One place to read the Shia hadith collections, look up the narrators, and follow the chains—without ever losing sight of the printed source.
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
            <h2 className="font-serif text-3xl font-semibold">What it is</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>The Shia hadith tradition runs to tens of thousands of narrations—the Four Books (Al-Kāfī, Man Lā Yaḥḍuruhu al-Faqīh, Tahdhīb al-Aḥkām, and al-Istibṣār) and centuries of collections after them. Most of it lives in dense scans, ageing websites, and scattered translations, where it&rsquo;s hard to tell how anything on screen relates to the book it came from.</p>
              <p>Usul16 brings it together and keeps it connected: the Arabic beside its English, each report beside its chain, every narrator&rsquo;s name beside who they actually were, and all of it beside the volume and page it was printed on.</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">How to read what you find</h2>
            <div className="mt-4 space-y-4 text-base leading-8 text-foreground/85">
              <p>The Arabic and the printed edition are the original. The English sits alongside to help you read it, named to its translator. Where we&rsquo;ve identified a narrator or mapped a chain, the evidence is shown so you can weigh it yourself.</p>
              <p>Nothing here asks you to take its word for it. Whatever you&rsquo;re looking at, the source is one click away.</p>
            </div>
          </section>

          <section className="border-t border-border pt-9">
            <h2 className="font-serif text-3xl font-semibold">Where it&rsquo;s going</h2>
            <p className="mt-4 text-base leading-8 text-foreground/85">The Four Books come first, done properly—clean text, real translations, and narrator profiles you can trust. Al-Kāfī is furthest along. From there, the same care extends through Biḥār al-Anwār and the wider tradition, one collection at a time.</p>
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
