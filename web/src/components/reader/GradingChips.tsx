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
    <div>
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
        Gradings
      </p>
      <ul className="flex flex-col gap-2">
        {gradings.map((grading, index) => {
          const sound = isSound(grading.grade_ar);
          return (
            <li
              key={`${grading.grader_key}-${index}`}
              className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm"
            >
              <span
                dir="rtl"
                lang="ar"
                className={`${amiri.className} inline-flex items-center rounded-sm px-2 py-0.5 text-base leading-none ${
                  sound
                    ? "bg-badge-verified text-badge-verified-foreground"
                    : "bg-badge text-badge-foreground"
                }`}
              >
                {grading.grade_ar || "—"}
              </span>
              <span className="text-foreground/80">{grading.author_name_en}</span>
              {grading.reference_en ? (
                <span className="text-xs text-muted">— {grading.reference_en}</span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
