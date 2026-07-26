import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { amiri } from "@/lib/fonts";
import { formatArabicText } from "@/lib/arabic";
import { ApiError } from "@/lib/api/client";
import { getTopicHadiths } from "@/lib/api/topics";
import { TopicChips, TopicTag } from "@/components/topics/TopicChips";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 50;

async function loadTopic(slug: string, page: number) {
  try {
    return await getTopicHadiths(slug, {
      skip: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const data = await loadTopic(decodeURIComponent(slug), 1);
  return {
    title: `${data.topic.name_en} - Hadith topics`,
    description: `${data.topic.hadith_count} narrations categorized under ${data.topic.name_en}.`,
    alternates: { canonical: `/topics/${encodeURIComponent(data.topic.slug)}` },
  };
}

export default async function TopicPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { slug } = await params;
  const query = await searchParams;
  const requestedPage = Number.parseInt(query.page ?? "1", 10);
  const page = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1;
  const data = await loadTopic(decodeURIComponent(slug), page);
  const pageCount = Math.max(1, Math.ceil(data.total / data.limit));

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header className="border-b border-border pb-6 sm:pb-8">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-muted">
          <Link href="/topics" className="hover:text-accent hover:underline">Hadith topics</Link>
          {data.parent ? (
            <>
              <span aria-hidden>/</span>
              <Link href={`/topics/${encodeURIComponent(data.parent.slug)}`} className="hover:text-accent hover:underline">
                {data.parent.name_en}
              </Link>
            </>
          ) : null}
        </nav>
        <h1 className="mt-4 max-w-4xl text-wrap-balance font-serif text-3xl font-semibold sm:text-4xl">
          {data.topic.name_en}
        </h1>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <TopicTag topic={data.topic} />
          <span className="text-sm text-muted">{data.total.toLocaleString()} narrations</span>
        </div>
      </header>

      {data.related_topics.length ? (
        <section className="border-b border-border py-6" aria-labelledby="related-heading">
          <h2 id="related-heading" className="text-sm font-semibold">Related topics</h2>
          <div className="mt-3 grid gap-x-8 gap-y-2 sm:grid-cols-2">
            {data.related_topics.map((topic) => (
              <Link key={topic.slug} href={`/topics/${encodeURIComponent(topic.slug)}`} className="flex min-w-0 items-baseline justify-between gap-4 py-1 text-sm text-muted hover:text-accent hover:underline">
                <span className="min-w-0 break-words">{topic.name_en}</span>
                <span className="shrink-0 tabular-nums">{topic.hadith_count}</span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section aria-label="Topic narrations" className="divide-y divide-border border-b border-border">
        {data.items.map((item) => (
          <article key={item.public_id} className="py-8">
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
              <Link href={`/hadith/${encodeURIComponent(item.public_id)}`} className="font-mono font-medium text-accent hover:underline">
                {item.public_id}
              </Link>
              <span className="text-muted">
                Vol. {item.volume_start ?? "?"}, p. {item.page_start}{item.page_end !== item.page_start ? `-${item.page_end}` : ""}
              </span>
            </div>
            <Link href={`/hadith/${encodeURIComponent(item.public_id)}`} className="mt-4 block focus-visible:outline-offset-4">
              <p dir="rtl" lang="ar" className={`${amiri.className} text-right text-xl leading-[2.1] text-foreground/90`}>
                {formatArabicText(item.matn_excerpt_ar)}
              </p>
              {item.translation_excerpt_en ? (
                <p className="mt-4 max-w-[72ch] leading-7 text-muted">{item.translation_excerpt_en}</p>
              ) : null}
            </Link>
            <div className="mt-4">
              <TopicChips topics={item.topics} compact />
            </div>
          </article>
        ))}
      </section>

      {pageCount > 1 ? (
        <nav aria-label="Topic result pages" className="mt-8 flex items-center justify-between gap-4">
          {page > 1 ? (
            <Link href={`?page=${page - 1}`} className="inline-flex min-h-11 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold hover:border-accent hover:text-accent">
              Previous
            </Link>
          ) : <span />}
          <span className="text-sm tabular-nums text-muted">Page {page} of {pageCount}</span>
          {page < pageCount ? (
            <Link href={`?page=${page + 1}`} className="inline-flex min-h-11 items-center rounded-md border border-border bg-surface px-4 text-sm font-semibold hover:border-accent hover:text-accent">
              Next
            </Link>
          ) : <span />}
        </nav>
      ) : null}
    </main>
  );
}
