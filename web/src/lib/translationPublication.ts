import type {
  HadithTranslationRead,
  TranslationPublicationEvidence,
} from "@/lib/api/types";

const PUBLIC_STATUSES = new Set(["human_reviewed", "published"]);
const PUBLIC_CLASSIFICATIONS = new Set([
  "external_source_normalized",
  "verbatim_external_matn_excerpt",
  "bounded_external_excerpt",
]);
const FORBIDDEN_MARKERS = [
  "codex",
  "openai",
  "gpt",
  "llm",
  "ai-generated",
  "ai_generated",
  "ai generated",
  "machine-generated",
  "machine_generated",
  "machine generated",
  "artificial intelligence",
  "project_authored",
  "project-authored",
  "project authored",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function provenanceText(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value ?? "");
  } catch {
    return String(value ?? "");
  }
}

export function hasPublicHumanSourceEvidence(
  value: unknown,
): value is TranslationPublicationEvidence {
  if (!isRecord(value)) return false;
  if (!PUBLIC_STATUSES.has(String(value.status ?? ""))) return false;
  if (value.risk_level !== "green") return false;
  if (
    Array.isArray(value.risk_flags) &&
    value.risk_flags.some(
      (flag) => isRecord(flag) && flag.severity === "critical",
    )
  ) {
    return false;
  }

  const provenance = value.provenance_json;
  if (!isRecord(provenance)) return false;
  const translator = provenance.translator;
  const classification =
    provenance.translation_classification ?? provenance.classification;
  if (typeof translator !== "string" || !translator.trim()) return false;
  if (
    typeof classification !== "string" ||
    !PUBLIC_CLASSIFICATIONS.has(classification)
  ) {
    return false;
  }

  const markerText = [value.provider, value.model, provenance]
    .map(provenanceText)
    .join(" ")
    .toLocaleLowerCase("en");
  return !FORBIDDEN_MARKERS.some((marker) => markerText.includes(marker));
}

export function isPublicHumanTranslation(
  value: unknown,
): value is HadithTranslationRead {
  if (!hasPublicHumanSourceEvidence(value) || !isRecord(value)) return false;
  return (
    typeof value.matn_translation === "string" &&
    Boolean(value.matn_translation.trim())
  );
}
