const ARABIC_DIGITS = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];

const EASTERN_ARABIC_DIGITS: Record<string, string> = {
  "۰": "٠",
  "۱": "١",
  "۲": "٢",
  "۳": "٣",
  "۴": "٤",
  "۵": "٥",
  "۶": "٦",
  "۷": "٧",
  "۸": "٨",
  "۹": "٩",
};

export interface PlateParts {
  letters: string;
  digits: string;
  summary: string;
}

export function toArabicDigits(value: string): string {
  return value.replace(/[0-9۰-۹]/g, (char) => EASTERN_ARABIC_DIGITS[char] ?? ARABIC_DIGITS[Number(char)] ?? char);
}

export function normalizePlateInput(value: string): string {
  return toArabicDigits(value)
    .replace(/\s+/g, " ")
    .trimStart();
}

export function formatPlateInput(value: string): string {
  return splitPlateChars(normalizePlateInput(value)).join(" ");
}

export function splitPlateChars(value?: string | null): string[] {
  return Array.from(value ?? "").filter((char) => char.trim().length > 0);
}

export function parsePlateInput(value?: string | null): PlateParts {
  const normalized = normalizePlateInput(value ?? "").trim();
  const chars = splitPlateChars(normalized);
  const letters = chars.filter((char) => !/[٠-٩]/.test(char)).join("");
  const digits = chars.filter((char) => /[٠-٩]/.test(char)).join("");
  const summary = [letters, digits].filter(Boolean).join(" ");
  return { letters, digits, summary };
}
