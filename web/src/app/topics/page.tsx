import type { Metadata } from "next";
import Link from "next/link";
import { getTopics } from "@/lib/api/topics";
import type { TopicSummary } from "@/lib/api/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Hadith topics",
  description: "Browse the hadith collections by moods, life situations, practices, virtues, beliefs, people, and source structure.",
  alternates: { canonical: "/topics" },
};

function TopicGroup({
  title,
  topics,
}: {
  title: string;
  topics: TopicSummary[];
}) {
  if (!topics.length) return null;
  return (
    <section className="border-b border-border py-8" aria-labelledby={`topics-${topics[0].kind}`}>
      <div className="flex items-baseline justify-between gap-4">
        <h2 id={`topics-${topics[0].kind}`} className="text-lg font-semibold">{title}</h2>
        <span className="text-sm tabular-nums text-muted">{topics.length}</span>
      </div>
      <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3">
        {topics.map((topic) => (
          <Link
            key={topic.slug}
            href={`/topics/${encodeURIComponent(topic.slug)}`}
            className="group flex min-h-16 items-center justify-between gap-4 border-t border-border px-1 py-3 transition-colors hover:bg-surface-2 sm:px-3"
          >
            <div className="min-w-0">
              <p className="font-medium text-foreground group-hover:text-accent">{topic.name_en}</p>
              <p className="mt-0.5 break-words text-xs text-muted">{topic.hashtag}</p>
            </div>
            <span className="shrink-0 text-xs tabular-nums text-muted">{topic.hadith_count.toLocaleString()}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default async function TopicsPage() {
  const [moods, life, practices, virtues, beliefs, people, kitabs] = await Promise.all([
    getTopics({ kind: "mood", limit: 100 }),
    getTopics({ kind: "life", limit: 100 }),
    getTopics({ kind: "practice", limit: 100 }),
    getTopics({ kind: "virtue", limit: 100 }),
    getTopics({ kind: "belief", limit: 100 }),
    getTopics({ kind: "person", limit: 100 }),
    getTopics({ kind: "kitab", limit: 100 }),
  ]);
  const semanticCount = moods.length + life.length + practices.length + virtues.length + beliefs.length + people.length;

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header className="border-b border-border pb-6 sm:pb-8">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className="font-serif text-3xl font-semibold sm:text-4xl">Explore the collections</h1>
            <p className="mt-3 max-w-[70ch] leading-7 text-muted">
              Moods, life situations, worship, character, beliefs, and each collection&apos;s original kitab structure.
            </p>
          </div>
          <Link href="/search" className="inline-flex min-h-11 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold hover:border-accent hover:text-accent">
            Search topics
          </Link>
        </div>
      </header>

      <div className="mt-4">
        <div className="flex items-baseline justify-between border-b border-border py-4 text-sm text-muted">
          <span>Searchable subjects</span>
          <span className="tabular-nums">{semanticCount.toLocaleString()}</span>
        </div>
        <TopicGroup title="Moods & inner states" topics={moods} />
        <TopicGroup title="Life & relationships" topics={life} />
        <TopicGroup title="Worship & practice" topics={practices} />
        <TopicGroup title="Character & virtues" topics={virtues} />
        <TopicGroup title="Belief & the hereafter" topics={beliefs} />
        <TopicGroup title="People & sacred history" topics={people} />
        <TopicGroup title="Collection structures" topics={kitabs} />
      </div>
    </main>
  );
}
