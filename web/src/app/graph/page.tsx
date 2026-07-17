import type { Metadata } from "next";
import { Suspense } from "react";
import { TransmissionGraphClient } from "@/components/graph/TransmissionGraphClient";
import { amiri } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "Transmission network",
  description:
    "The transmission network of Al-Kafi: every confident narrator-to-narrator link, drawn as an interactive map.",
};

export default function GraphPage() {
  return (
    <div className="mx-auto max-w-[90rem] px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
      <header className="mb-8 grid gap-8 border-b border-border pb-8 lg:grid-cols-[minmax(0,1fr)_19rem] lg:items-end">
        <div>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-2xl text-accent`}>
          شبكة الرواة
        </p>
        <h1 className="mt-2 font-serif text-5xl font-semibold tracking-[-0.025em] sm:text-6xl">Follow the transmission.</h1>
        <p className="mt-4 max-w-3xl leading-7 text-muted">
          Explore confident narrator-to-narrator links in al-Kāfī as an evidence-backed map. Select a narrator to inspect their profile; select a connection to return to the hadiths that establish it.
        </p>
        </div>
        <aside className="border-t border-border pt-5 text-sm lg:border-l lg:border-t-0 lg:pl-6">
          <p className="font-semibold text-foreground">How to read the map</p>
          <p className="mt-2 leading-6 text-muted">Node colour indicates generation; line weight reflects repeated transmission. Ambiguous chains are withheld from the confident view.</p>
        </aside>
      </header>

      <Suspense fallback={null}>
        <TransmissionGraphClient />
      </Suspense>
    </div>
  );
}
