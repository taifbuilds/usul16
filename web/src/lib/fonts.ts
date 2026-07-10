import { Amiri } from "next/font/google";

// Shared across every component that renders Arabic/Persian text (reader
// body, book titles) so the font-face is declared once, not re-created per
// component. Importing this module is itself what triggers next/font to
// include the font — pages that never import it pay nothing for it.
export const amiri = Amiri({
  subsets: ["arabic"],
  weight: ["400", "700"],
  display: "swap",
  variable: "--font-amiri",
});
