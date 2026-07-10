import { getStats } from "@/lib/api/stats";

export const dynamic = "force-dynamic";

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <p className="font-serif text-4xl text-foreground">{value.toLocaleString()}</p>
      <p className="mt-1 text-xs font-semibold tracking-wide text-muted uppercase">{label}</p>
    </div>
  );
}

export default async function AboutPage() {
  const stats = await getStats();

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <p className="text-sm font-semibold tracking-wide text-accent uppercase">About the project</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight sm:text-5xl">
        A quiet reader for a vast tradition.
      </h1>
      <div className="mt-6 h-px w-24 bg-gradient-to-r from-accent to-gold" />

      <div className="mt-8 space-y-5 text-foreground/90">
        <p>
          The Shia hadith corpus spans tens of thousands of traditions across the Four Books — al-Kāfī, Man Lā
          Yaḥḍuruhu al-Faqīh, Tahdhīb al-Aḥkām, and al-Istibṣār — plus centuries of secondary collections. Most
          of it lives in dense printed volumes or aging websites that are hard to read and harder to search.
        </p>
        <p>
          <strong className="font-medium text-foreground">Usul16</strong> is a small project with one goal:
          make this corpus a pleasure to read. Every page is presented in its original Arabic — the chain, the
          text, and the footnotes of the critical edition — with a citation back to the printed volume and
          page.
        </p>
        <p>
          Nothing is behind a login. There is no account to create. If it helps one student, one researcher, or
          one curious reader find what they were looking for, it has done its job.
        </p>
      </div>

      <div className="mt-12 grid grid-cols-3 gap-6 border-t border-border pt-8">
        <Stat value={stats.pages_digitized} label="Pages digitized" />
        <Stat value={stats.books_readable} label="Books readable" />
        <Stat value={stats.authors} label="Authors indexed" />
      </div>
    </div>
  );
}
