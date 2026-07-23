import type { Metadata, Viewport } from "next";
import { Instrument_Sans, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/nav/SiteHeader";
import { SiteFooter } from "@/components/nav/SiteFooter";
import { themeInitScript } from "@/components/ui/ThemeToggle";
import { amiri } from "@/lib/fonts";
import { dir } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { getLocale } from "@/lib/i18n/locale";

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

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  const en = {
    title: "Usul16 — Shia hadith research library",
    description:
      "Read Al-Kāfī and the major Shia hadith collections in Arabic and English, look up any narrator, and trace every chain—all linked back to the printed page.",
    ogDescription:
      "Read the major Shia hadith collections in Arabic and English, look up the narrators, and follow the chains—linked to the printed source.",
  };
  const ar = {
    title: "أصول ١٦ — مكتبة بحوث الحديث الشيعي",
    description:
      "اقرأ الكافي وأمّهات مصنَّفات الحديث الشيعي بالعربية والإنجليزية، وابحث في تراجم الرواة، وتتبَّع كلّ سند — والكلّ موصولٌ بالصفحة المطبوعة.",
    ogDescription:
      "اقرأ أمّهات مصنَّفات الحديث الشيعي بالعربية والإنجليزية، وابحث في تراجم الرواة، وتتبَّع الأسانيد — موصولةً بالمصدر المطبوع.",
  };
  const t = locale === "ar" ? ar : en;
  return {
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
    title: { default: t.title, template: "%s — Usul16" },
    description: t.description,
    applicationName: "Usul16",
    authors: [{ name: "Usul16" }],
    openGraph: { type: "website", siteName: "Usul16", title: t.title, description: t.ogDescription },
    twitter: { card: "summary", title: t.title },
  };
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#182720" },
    { media: "(prefers-color-scheme: light)", color: "#f4eee1" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  const t = getDictionary(locale);
  return (
    <html
      lang={locale}
      dir={dir(locale)}
      suppressHydrationWarning
      className={`${instrumentSans.variable} ${sourceSerif.variable} ${amiri.variable} h-full antialiased`}
    >
      <body className="relative flex min-h-full flex-col bg-background text-foreground">
        {/* Sets data-theme before first paint to avoid a flash of the wrong theme. */}
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <SiteHeader locale={locale} nav={t.nav} />
        <main id="main-content" className="relative flex-1">{children}</main>
        <SiteFooter foot={t.footer} />
      </body>
    </html>
  );
}
