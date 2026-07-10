"use client";

import { ErrorMessage } from "@/components/ui/ErrorMessage";

export default function Error({ unstable_retry }: { error: Error & { digest?: string }; unstable_retry: () => void }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <ErrorMessage title="Search failed" description="The backend API may be unreachable." onRetry={unstable_retry} />
    </div>
  );
}
