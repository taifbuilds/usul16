// Inline decorations shared by the server-rendered reader text and the
// interactive hadith body: footnote refs "[١]"/"[1]" and honorific formulae.
// Variants cover both ZWNJ-joined and space-separated spellings, plus the
// bare "ع" abbreviation used by the Islamiyya edition.
export const INLINE_RE =
  /(\[\s*[0-9٠-٩]+\s*\])|(صلى‌الله‌عليه‌وآله‌وسلم|صلى‌الله‌عليه‌وآله|صلى الله عليه وآله وسلم|صلى الله عليه وآله|عليه‌السلام|عليه السلام|عليها‌السلام|عليها السلام|عليهما‌السلام|عليهما السلام|عليهم‌السلام|عليهم السلام|رضي‌الله‌عنه|رضي الله عنه|رحمه‌الله|رحمه الله|(?<=[\s(])ع(?=[\s‌)،.؟!:]|$))/g;

const ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩";

/** "٤" -> "4"; leaves western digits alone. Used to match footnote markers
 * across the two digit systems. */
export function toWesternDigits(value: string): string {
  return value.replace(/[٠-٩]/g, (ch) => String(ARABIC_DIGITS.indexOf(ch)));
}

export function normaliseMarker(value: string): string {
  return toWesternDigits(value).replace(/[^0-9]/g, "");
}
