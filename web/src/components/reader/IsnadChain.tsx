import { amiri } from "@/lib/fonts";
import { GradeBadge, type Grade } from "@/components/reader/GradeBadge";

interface Transmitter {
  nameEn: string;
  nameAr: string;
  grade: Grade;
  note: string;
}

// A real, well-known chain (al-Kafi, Bab fadl al-'aql, hadith 1) used purely
// as an illustrative preview of this component's design. The crawler stores
// page prose, not per-hadith transmitter records, so there is no isnad data
// to attach per page yet — see the caption rendered below the list.
const SAMPLE_CHAIN: Transmitter[] = [
  { nameEn: "Muḥammad ibn Yaʿqūb al-Kulaynī", nameAr: "محمد بن يعقوب الكليني", grade: "sahih", note: "The compiler — ṣāḥib al-Kāfī" },
  { nameEn: "ʿAlī ibn Ibrāhīm al-Qummī", nameAr: "علي بن إبراهيم القمي", grade: "thiqa", note: "Thiqah, ṣāḥib al-tafsīr" },
  { nameEn: "Ibrāhīm ibn Hāshim al-Qummī", nameAr: "إبراهيم بن هاشم القمي", grade: "thiqa", note: "Thiqah — first to spread Kufan ḥadīth in Qum" },
  { nameEn: "Muḥammad ibn ʿĪsā ibn ʿUbayd", nameAr: "محمد بن عيسى بن عبيد", grade: "companion", note: "Companion of al-Riḍā and al-Jawād (ʿa)" },
  { nameEn: "Yūnus ibn ʿAbd al-Raḥmān", nameAr: "يونس بن عبد الرحمن", grade: "thiqa", note: "Thiqah — companion of al-Kāẓim and al-Riḍā (ʿa)" },
];

export function IsnadChain() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6">
      <div className="flex items-baseline justify-between">
        <p className="text-sm font-semibold tracking-wide text-muted uppercase">Chain of narration</p>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-lg text-accent`}>
          السند
        </p>
      </div>
      <p className="mt-1 text-sm text-muted">
        {SAMPLE_CHAIN.length} transmitters, from the compiler up to Imam al-Ṣādiq (ʿa).
      </p>

      <ol className="mt-6 space-y-6 border-l border-border pl-6">
        {SAMPLE_CHAIN.map((t, index) => (
          <li key={t.nameEn} className="relative">
            <span className="absolute -left-[calc(1.5rem+0.5rem)] flex h-6 w-6 items-center justify-center rounded-full border border-border bg-background text-xs font-medium text-muted">
              {index + 1}
            </span>
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <p className="font-medium text-foreground">{t.nameEn}</p>
              <p dir="rtl" lang="ar" className={`${amiri.className} text-base text-muted`}>
                {t.nameAr}
              </p>
            </div>
            <div className="mt-1.5 flex items-center gap-2">
              <GradeBadge grade={t.grade} />
              <span className="text-sm text-muted">{t.note}</span>
            </div>
          </li>
        ))}
      </ol>

      <p className="mt-6 border-t border-border pt-3 text-xs text-muted italic">
        Sample chain shown for design preview — per-page narrator data isn&apos;t linked in this mirror yet.
      </p>
    </div>
  );
}
