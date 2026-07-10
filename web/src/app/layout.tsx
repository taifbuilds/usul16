import type { Metadata } from "next";
import { Fraunces, Instrument_Sans } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/nav/SiteHeader";
import { SiteFooter } from "@/components/nav/SiteFooter";

// Arabic font (next/font/google) is intentionally NOT loaded here — see
// components that render Arabic text, which import it directly so pages
// with no Arabic content don't pay for that font's weight.
const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-body",
});

// Warm, literary display serif for headings — the "quiet reading room" feel
// comes mostly from pairing this against a clean grotesque for UI chrome.
const fraunces = Fraunces({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "Usul16 — The Shia Hadith Library",
  description:
    "Read and search the hadith of the Prophet and the Ahl al-Bayt — the Four Books and centuries of collections, in their original Arabic.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" dir="ltr" className={`${instrumentSans.variable} ${fraunces.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
