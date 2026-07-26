import Link from "next/link";
import type { HadithTopic } from "@/lib/api/types";

type TopicLinkData = Pick<HadithTopic, "slug" | "hashtag" | "name_en" | "kind">;

export function TopicTag({
  topic,
  compact = false,
}: {
  topic: TopicLinkData;
  compact?: boolean;
}) {
  const label = topic.hashtag.replace(/^#/, "");

  return (
    <Link
      href={`/topics/${encodeURIComponent(topic.slug)}`}
      title={topic.name_en}
      aria-label={`${topic.hashtag}: ${topic.name_en}`}
      data-topic-kind={topic.kind}
      dir="ltr"
      className={`topic-index__item ${compact ? "topic-index__item--compact" : ""}`}
    >
      <span aria-hidden="true" className="topic-index__mark">#</span>
      <span aria-hidden="true" className="topic-index__label">{label}</span>
    </Link>
  );
}

export function TopicChips({
  topics,
  compact = false,
}: {
  topics: HadithTopic[];
  compact?: boolean;
}) {
  if (!topics.length) return null;

  return (
    <nav aria-label="Hadith topics" className="topic-index">
      {topics.map((topic) => (
        <TopicTag key={topic.slug} topic={topic} compact={compact} />
      ))}
    </nav>
  );
}
