export type Grade = "sahih" | "thiqa" | "companion" | "muttasil" | "marfu";

const LABELS: Record<Grade, string> = {
  sahih: "Ṣaḥīḥ",
  thiqa: "Thiqah",
  companion: "Companion",
  muttasil: "Muttaṣil",
  marfu: "Marfūʿ",
};

export function GradeBadge({ grade }: { grade: Grade }) {
  const label = LABELS[grade];

  if (grade === "sahih") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-badge-verified px-2.5 py-0.5 text-xs font-medium text-badge-verified-foreground">
        <span aria-hidden>✓</span>
        {label}
      </span>
    );
  }

  return (
    <span className="rounded-full bg-badge px-2.5 py-0.5 text-xs font-medium text-badge-foreground">{label}</span>
  );
}
