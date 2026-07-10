import Link from "next/link";

export function Pagination({
  basePath,
  skip,
  limit,
  hasMore,
  extraParams = {},
}: {
  basePath: string;
  skip: number;
  limit: number;
  hasMore: boolean;
  extraParams?: Record<string, string>;
}) {
  function hrefFor(newSkip: number) {
    const params = new URLSearchParams(extraParams);
    if (newSkip > 0) params.set("skip", String(newSkip));
    const query = params.toString();
    return query ? `${basePath}?${query}` : basePath;
  }

  const prevSkip = Math.max(0, skip - limit);
  const hasPrev = skip > 0;

  return (
    <div className="flex items-center justify-between pt-4">
      {hasPrev ? (
        <Link href={hrefFor(prevSkip)} className="text-sm font-medium text-accent hover:underline">
          ← Previous
        </Link>
      ) : (
        <span />
      )}
      {hasMore ? (
        <Link href={hrefFor(skip + limit)} className="text-sm font-medium text-accent hover:underline">
          Next →
        </Link>
      ) : (
        <span />
      )}
    </div>
  );
}
