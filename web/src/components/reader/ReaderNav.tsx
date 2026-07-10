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
    <div className="flex items-center justify-between border-t border-border pt-4 text-sm">
      {prev ? (
        <Link href={prev.href} className="font-medium text-accent hover:underline">
          ← {prev.label}
        </Link>
      ) : (
        <span className="text-muted">← {/* start of book */}</span>
      )}
      <span className="text-muted">{position}</span>
      {next ? (
        <Link href={next.href} className="font-medium text-accent hover:underline">
          {next.label} →
        </Link>
      ) : (
        <span className="text-muted">{/* end of book */} →</span>
      )}
    </div>
  );
}
