import type { Metadata } from "next";
import { Suspense } from "react";
import { TransmissionGraphClient } from "@/components/graph/TransmissionGraphClient";
import { amiri } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "The Network — usul16",
  description:
    "The transmission network of Al-Kafi: every confident narrator-to-narrator link, drawn as an interactive map.",
};

export default function GraphPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <header className="mb-6 max-w-3xl">
        <p dir="rtl" lang="ar" className={`${amiri.className} text-lg text-gold`}>
          شبكة الرواة
        </p>
        <h1 className="mt-1 font-serif text-4xl tracking-tight">The Transmission Network</h1>
        <p className="mt-3 text-muted">
          Every confident narrator-to-narrator link in al-Kāfī, drawn as one map. Gold suns are
          the Imams; narrators are shaded by their estimated ṭabaqa (generation), from the
          luminous earliest layers to the deep blue of the compilers&apos; era. Line weight is how
          many hadiths two narrators share. Identities merged by al-Khoei&apos;s own rulings appear
          as a single star. Ambiguous chains are not drawn — this map shows only what the
          resolver is confident about.
        </p>
      </header>

      <Suspense fallback={null}>
        <TransmissionGraphClient />
      </Suspense>
    </main>
  );
}
