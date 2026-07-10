"use client";

export function ErrorMessage({
  title = "Something went wrong",
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface px-6 py-8 text-center">
      <p className="font-medium text-foreground">{title}</p>
      {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-full border border-border px-4 py-1.5 text-sm font-medium hover:bg-border/40"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}
