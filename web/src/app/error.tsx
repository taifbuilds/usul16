"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[55vh] max-w-2xl flex-col justify-center px-4 py-16 sm:px-6">
      <p className="text-sm font-semibold text-accent">Research service unavailable</p>
      <h1 className="mt-3 font-serif text-4xl font-semibold">This record could not be loaded.</h1>
      <p className="mt-4 max-w-xl leading-7 text-muted">The source data may be temporarily unreachable. Your location is unchanged; retry the request or return to a stable research path.</p>
      <div className="mt-7 flex flex-wrap gap-3">
        <button type="button" onClick={reset} className="inline-flex min-h-11 items-center rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground">Try again</button>
        <Link href="/search" className="inline-flex min-h-11 items-center rounded-md border border-border-strong px-5 text-sm font-semibold hover:border-accent hover:text-accent">Search the corpus</Link>
      </div>
    </div>
  );
}
