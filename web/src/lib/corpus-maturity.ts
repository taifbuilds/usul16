export type CorpusMaturity = {
  label: string;
  tone: "audited" | "review" | "preview" | "reference";
  summary: string;
};

export const CORPUS_MATURITY: Record<string, CorpusMaturity> = {
  "11005": {
    label: "Al-Kafi research beta",
    tone: "audited",
    summary: "Hadith boundaries reconciled; parsed chains currently have no outstanding review flags.",
  },
  "11021": {
    label: "Structured · under review",
    tone: "review",
    summary: "Readable and structured; chain review and editorial reconciliation are still in progress.",
  },
  "10083": {
    label: "Structured · under review",
    tone: "review",
    summary: "Readable and structured; chain review and editorial reconciliation are still in progress.",
  },
  "11002": {
    label: "Structured · under review",
    tone: "review",
    summary: "Readable and structured; chain review and editorial reconciliation are still in progress.",
  },
  "71860": {
    label: "Research preview",
    tone: "preview",
    summary: "Large parsed corpus with substantial chain review still outstanding.",
  },
  "11025": {
    label: "Page-text edition",
    tone: "preview",
    summary: "Source pages are readable; hadith-level extraction is not yet published.",
  },
  "14036": {
    label: "Rijal reference",
    tone: "reference",
    summary: "Reference pages and narrator evidence support identity research; not a hadith collection.",
  },
};

export const COLLECTION_NAMES: Record<string, string> = {
  "11005": "Al-Kafi",
  "11021": "Man La Yahduruhu al-Faqih",
  "10083": "Tahdhib al-Ahkam",
  "11002": "Al-Istibsar",
  "71860": "Bihar al-Anwar",
  "11025": "Wasa'il al-Shia",
  "14036": "Mu'jam Rijal al-Hadith",
};

export function corpusMaturity(sourceBookId: string): CorpusMaturity | null {
  return CORPUS_MATURITY[sourceBookId] ?? null;
}
