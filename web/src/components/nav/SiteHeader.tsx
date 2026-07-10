import Link from "next/link";

const NAV_LINKS = [
  { href: "/books", label: "The Books" },
  { href: "/graph", label: "The Network" },
  { href: "/search", label: "Search" },
  { href: "/about", label: "About" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-6 px-4 py-3.5 sm:px-6">
        <Link href="/" className="font-serif text-2xl tracking-tight whitespace-nowrap">
          usul<span className="text-accent">16</span>
        </Link>

        <nav className="flex flex-1 flex-wrap items-center gap-6 text-sm text-foreground/80">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="transition hover:text-accent">
              {link.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/books"
          className="ml-auto rounded-full bg-foreground px-5 py-2 text-sm font-medium text-background transition hover:-translate-y-px hover:opacity-85"
        >
          Start reading →
        </Link>
      </div>
    </header>
  );
}
