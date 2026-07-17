import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Narrator profile",
  robots: { index: true, follow: true },
};

export default function NarratorLayout({ children }: { children: React.ReactNode }) {
  return children;
}
