import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[55vh] max-w-2xl flex-col justify-center px-4 py-16 sm:px-6">
      <p className="text-sm font-semibold text-accent">Record not found</p>
      <h1 className="mt-3 font-serif text-4xl font-semibold">This source location is not available.</h1>
      <p className="mt-4 max-w-xl leading-7 text-muted">The link may be outdated, the record may be under review, or this part of the edition has not yet been digitised.</p>
      <div className="mt-7 flex flex-wrap gap-3">
        <Link href="/search" className="inline-flex min-h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground">Search the corpus</Link>
        <Link href="/books" className="inline-flex min-h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">Browse the library</Link>
      </div>
    </div>
  );
}
