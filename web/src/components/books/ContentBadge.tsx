export function ContentBadge({ hasContent }: { hasContent: boolean }) {
  return hasContent ? (
    <span className="rounded-full bg-badge-verified px-2.5 py-0.5 text-xs font-medium text-badge-verified-foreground">
      Full text available
    </span>
  ) : (
    <span className="rounded-full bg-badge px-2.5 py-0.5 text-xs font-medium text-badge-foreground">
      Catalog only
    </span>
  );
}
