import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6">
      <h1 className="text-xl font-semibold">Book not found</h1>
      <p className="mt-2 text-muted">This book doesn&apos;t exist in the mirror.</p>
      <Link href="/books" className="mt-4 inline-block font-medium text-accent hover:underline">
        ← Back to browse
      </Link>
    </div>
  );
}
