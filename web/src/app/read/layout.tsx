import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Source reader",
};

export default function ReaderLayout({ children }: { children: React.ReactNode }) {
  return children;
}
