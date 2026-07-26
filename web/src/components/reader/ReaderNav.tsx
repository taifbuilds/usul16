import Link from "next/link";

export interface NavTarget {
  href: string;
  label: string;
}

export function ReaderNav({
  prev,
  next,
  position,
}: {
  prev: NavTarget | null;
  next: NavTarget | null;
  position: string;
}) {
  return (
    <nav aria-label="Reader pages" className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 border-t border-border pt-4 text-sm">
      {prev ? (
        <Link href={prev.href} className="min-w-0 truncate font-medium text-accent hover:underline">
          ← {prev.label}
        </Link>
      ) : (
        <span className="text-muted">←</span>
      )}
      <span className="whitespace-nowrap text-center text-xs text-muted sm:text-sm">{position}</span>
      {next ? (
        <Link href={next.href} className="min-w-0 truncate text-right font-medium text-accent hover:underline">
          {next.label} →
        </Link>
      ) : (
        <span className="text-right text-muted">→</span>
      )}
    </nav>
  );
}
