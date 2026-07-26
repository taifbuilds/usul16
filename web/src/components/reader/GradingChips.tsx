import type { HadithGrading } from "@/lib/api/types";
import { amiri } from "@/lib/fonts";

// Grades that assert soundness/reliability. These read as bronze "evidence"
// chips; every other verdict stays neutral. This is the grader's judgment,
// attributed to them — never presented as the project's own ruling.
const SOUND_GRADES = ["صحيح", "حسن", "موثق", "قوي", "معتبر"];

function isSound(gradeAr: string): boolean {
  return SOUND_GRADES.some((g) => gradeAr.includes(g));
}

export function GradingChips({ gradings }: { gradings: HadithGrading[] }) {
  return (
    <section aria-labelledby="hadith-gradings-heading">
      <div className="mb-2 flex items-center justify-between gap-4">
        <h3 id="hadith-gradings-heading" className="text-sm font-semibold text-foreground">
          Hadith gradings
        </h3>
        <span className="text-xs tabular-nums text-muted">{gradings.length}</span>
      </div>
      <ul className="divide-y divide-border border-y border-border">
        {gradings.map((grading, index) => {
          const sound = isSound(grading.grade_ar);
          return (
            <li
              key={`${grading.grader_key}-${index}`}
              className="grid gap-2 py-2.5 text-sm sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center sm:gap-3"
            >
              <span
                dir="rtl"
                lang="ar"
                className={`${amiri.className} inline-flex w-fit items-center rounded-sm px-2 py-1 text-base leading-none ${
                  sound
                    ? "bg-badge-verified text-badge-verified-foreground"
                    : "bg-badge text-badge-foreground"
                }`}
              >
                {grading.grade_ar || "—"}
              </span>
              <span className="font-medium text-foreground/80">{grading.author_name_en}</span>
              {grading.reference_en ? (
                <span className="text-xs text-muted sm:text-right">{grading.reference_en}</span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
