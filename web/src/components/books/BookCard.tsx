import Image from "next/image";
import Link from "next/link";
import { amiri } from "@/lib/fonts";
import { formatArabicTitle } from "@/lib/arabic";
import type { BookSummary } from "@/lib/api/types";
import { corpusMaturity } from "@/lib/corpus-maturity";

type CoverRecord = {
  label: string;
  src?: string;
};

/**
 * Cover images are scans or photographs of the edition represented by the
 * source record. Never add a designed substitute here: an honest archival
 * placeholder is preferable to a plausible but fabricated binding.
 */
const EDITION_COVERS: Record<string, CoverRecord> = {
  "11005": { label: "Al-Kafi", src: "/covers/eshia/11005.jpg" },
  "11021": { label: "Man La Yahduruhu al-Faqih", src: "/covers/eshia/11021.jpg" },
  "10083": { label: "Tahdhib al-Ahkam", src: "/covers/eshia/10083.jpg" },
  "11002": { label: "Al-Istibsar", src: "/covers/eshia/11002.jpg" },
  "71860": { label: "Bihar al-Anwar", src: "/covers/eshia/71860.jpg" },
  "11025": { label: "Wasa'il al-Shia", src: "/covers/eshia/11025.jpg" },
  "14036": { label: "Mu'jam Rijal al-Hadith" },
  "14028": { label: "Rijal al-Najashi", src: "/covers/eshia/14028.jpg" },
  "71743": { label: "Ayat al-Ahkam", src: "/covers/eshia/71743.jpg" },
  "10241": { label: "Rijal al-Kashshi" },
  "12146": { label: "Rijal al-Tusi" },
  "13341": { label: "Rijal Ibn Dawud" },
  "27182": { label: "Kulliyat fi Ilm al-Rijal" },
  "14010": { label: "Al-Fihrist" },
  "12147": { label: "Rijal al-Allama al-Hilli" },
  "86758": { label: "Rijal al-Barqi" },
};

export function BookCard({ book, index = 0 }: { book: BookSummary; index?: number }) {
  const title = formatArabicTitle(book.title_original);
  const cover = EDITION_COVERS[book.source_book_id];
  const maturity = corpusMaturity(book.source_book_id);
  const label = cover?.label ?? title;
  const volumes = book.volume_count
    ? `${book.volume_count} ${book.volume_count === 1 ? "volume" : "volumes"}`
    : null;

  return (
    <Link
      href={`/books/${book.id}`}
      aria-label={`Open ${label}`}
      className="library-book group/book"
    >
      <span className="library-book__object">
        <span aria-hidden className="library-book__shadow" />
        <span aria-hidden className="library-book__page-block">
          <span className="library-book__page-lines" />
        </span>

        <span className={`library-book__cover ${cover?.src ? "" : "library-book__cover--unavailable"}`}>
          {cover?.src ? (
            <Image
              src={cover.src}
              alt={`${label} — cover of the catalogued edition`}
              fill
              priority={index < 4}
              sizes="(max-width: 639px) 78vw, (max-width: 1023px) 38vw, 18rem"
              className="library-book__cover-image"
            />
          ) : (
            <span className="library-book__unavailable">
              <span className="library-book__source-id">Source {book.source_book_id}</span>
              <span dir="rtl" lang="ar" className={`${amiri.className} library-book__unavailable-title`}>
                {title}
              </span>
              <span className="library-book__unavailable-note">Cover scan unavailable</span>
            </span>
          )}
          <span aria-hidden className="library-book__cover-sheen" />
        </span>

        <span aria-hidden className="library-book__edge" />
        <span aria-hidden className="library-book__open-cue">
          Open
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M4 10h12M12 6l4 4-4 4" />
          </svg>
        </span>
      </span>

      <span className="library-book__caption">
        <span className="min-w-0">
          <span className="library-book__label">{label}</span>
          <span className="library-book__provenance">
            {cover?.src ? "Edition cover" : "Cover not supplied"}
            {volumes ? <><span aria-hidden> · </span>{volumes}</> : null}
          </span>
          {maturity ? <span className="mt-1 block text-xs font-semibold text-[color:var(--stage-accent)]">{maturity.label}</span> : null}
        </span>
        <span className="library-book__open-label" aria-hidden>
          Open
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M4 10h12M12 6l4 4-4 4" />
          </svg>
        </span>
      </span>
    </Link>
  );
}
