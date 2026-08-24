import type { Metadata } from "next";
import { Suspense } from "react";
import { TransmissionGraphClient } from "@/components/graph/TransmissionGraphClient";
import { amiri } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "Transmission network",
  description:
    "Explore confident narrator-to-narrator links across Al-Kafi and Man La Yahduruhu al-Faqih.",
};

export default function GraphPage() {
  return (
    <div className="mx-auto max-w-[90rem] px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header className="mb-7 grid gap-6 border-b border-border pb-7 lg:grid-cols-[minmax(0,1fr)_19rem] lg:items-end">
        <div>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-2xl text-accent`}>
          شبكة الرواة
        </p>
        <h1 className="mt-2 font-serif text-4xl font-semibold leading-tight sm:text-5xl">Follow the transmission.</h1>
        <p className="mt-4 max-w-3xl leading-7 text-muted">
          Explore confident narrator-to-narrator links across al-Kāfī and Man Lā Yaḥḍuruhu al-Faqīh. Filter by collection, select a narrator to inspect their profile, or open a connection to see the hadiths that establish it.
        </p>
        </div>
        <aside className="border-t border-border pt-5 text-sm lg:border-l lg:border-t-0 lg:pl-6">
          <p className="font-semibold text-foreground">How to read the map</p>
          <p className="mt-2 leading-6 text-muted">Node colour shows an anchored generation when one is available; inferred generations stay undated. Lines show adjacent resolved names in an isnad, not proof of historical hearing. Ambiguous chains are withheld from the confident view.</p>
        </aside>
      </header>

      <Suspense fallback={null}>
        <TransmissionGraphClient />
      </Suspense>
    </div>
  );
}
