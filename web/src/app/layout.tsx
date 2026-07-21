import type { Metadata, Viewport } from "next";
import { Instrument_Sans, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/nav/SiteHeader";
import { SiteFooter } from "@/components/nav/SiteFooter";
import { themeInitScript } from "@/components/ui/ThemeToggle";

// Arabic font (next/font/google) is intentionally NOT loaded here — see
// components that render Arabic text, which import it directly so pages
// with no Arabic content don't pay for that font's weight.
const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-body",
});

// Warm, literary display serif for headings — the editorial character comes
// mostly from pairing this against a clean grotesque for UI chrome.
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: {
    default: "Usul16 — Shia hadith research library",
    template: "%s — Usul16",
  },
  description:
    "Read Al-Kāfī and the major Shia hadith collections in Arabic and English, look up any narrator, and trace every chain—all linked back to the printed page.",
  applicationName: "Usul16",
  authors: [{ name: "Usul16" }],
  openGraph: {
    type: "website",
    siteName: "Usul16",
    title: "Usul16 — Shia hadith research library",
    description: "Read the major Shia hadith collections in Arabic and English, look up the narrators, and follow the chains—linked to the printed source.",
  },
  twitter: { card: "summary", title: "Usul16 — Shia hadith research library" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#182720" },
    { media: "(prefers-color-scheme: light)", color: "#f4eee1" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      dir="ltr"
      suppressHydrationWarning
      className={`${instrumentSans.variable} ${sourceSerif.variable} h-full antialiased`}
    >
      <body className="relative flex min-h-full flex-col bg-background text-foreground">
        {/* Sets data-theme before first paint to avoid a flash of the wrong theme. */}
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <SiteHeader />
        <main id="main-content" className="relative flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
