const PERSIAN_TITLE_MARKERS = [
  /[\u067e\u0686\u0698\u06af]/,
  /\u0622\u0634\u0646\u0627\u06cc\u06cc/,
  /\u0627\u062d\u06a9\u0627\u0645/,
  /\u062e\u0627\u0646\u0648\u0627\u062f\u0647/,
  /\u0646\u0645\u0627\u0632/,
  /\u0631\u0648\u0632\u0647/,
  /\u0628\u0627\u0646\u0648\u0627\u0646/,
  /\u0627\u0646\u062f\u06cc\u0634\u0647/,
  /\s\u062f\u0631\s/,
  /\s\u0628\u0627\s/,
];

export function looksPersianTitle(value: string): boolean {
  return PERSIAN_TITLE_MARKERS.some((marker) => marker.test(value));
}

export function formatArabicTitle(value: string): string {
  if (looksPersianTitle(value)) return value;
  return formatArabicText(value);
}

export function formatArabicText(value: string): string {
  return value.replace(/\u06a9/g, "\u0643").replace(/\u06cc/g, "\u064a");
}
