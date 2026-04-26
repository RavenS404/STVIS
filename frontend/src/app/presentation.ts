import type { CaseDetail, CaseListItem, CasePlateRead, CaseViolation, UserRole } from "./types";

export const BRAND_SHORT = "ITVM";
export const BRAND_NAME = "Intelligent Traffic Violation Monitoring for Reliable and Affordable Road Safety";
export const BRAND_TAGLINE_AR = "منصة ذكية لمراقبة المخالفات المرورية وإصدارها بشكل موثوق وبتكلفة مناسبة";

const STATE_LABELS: Record<string, string> = {
  direct_issue_ready: "جاهزة للإصدار",
  supervisor_review_required: "بحاجة إلى مشرف",
  issued: "تم الإصدار",
  rejected: "مرفوضة",
  no_violation: "لا توجد مخالفة",
  ok: "سليم",
  warning: "تنبيه",
  error: "خطأ",
  unknown: "غير معروف",
};

const ASSOCIATION_LABELS: Record<string, string> = {
  confident: "ربط مؤكد",
  ambiguous: "ربط غير محسوم",
  doubtful: "ربط يحتاج مراجعة",
};

const VIOLATION_LABELS: Record<string, string> = {
  unfastened_seat_belt: "عدم ربط حزام الأمان",
  using_mobile: "استخدام الهاتف أثناء القيادة",
  wrong_way: "السير عكس الاتجاه",
  seat_belt_present: "حزام الأمان ظاهر",
};

const FLAG_LABELS: Record<string, string> = {
  plate_missing: "لا توجد لوحة مؤكدة",
  plate_low_confidence: "قراءة اللوحة ضعيفة",
  plate_review_threshold: "قراءة اللوحة تحتاج مراجعة",
  multiple_plate_candidates: "تم رصد أكثر من لوحة محتملة",
  plate_association_ambiguous: "ربط اللوحة بالمركبة غير محسوم",
  plate_association_doubtful: "ربط اللوحة بالمركبة ضعيف",
  no_actionable_violation: "لا توجد مخالفة قابلة للإصدار",
};

function humanizeLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\s+/g, " ").trim();
}

function violationLabelFromCode(code: string): string {
  return VIOLATION_LABELS[code] ?? humanizeLabel(code);
}

export function translateState(state: string): string {
  return STATE_LABELS[state] ?? humanizeLabel(state);
}

export function translateAssociationStatus(state?: string | null): string {
  if (!state) return "غير متاح";
  return ASSOCIATION_LABELS[state] ?? humanizeLabel(state);
}

export function translateRole(role?: UserRole | null): string {
  if (role === "admin") return "إدارة كاملة";
  if (role === "supervisor") return "إشراف عمليات";
  return "مستخدم";
}

export function formatCaseNumber(caseNumber: string): string {
  return caseNumber.replace(/^STVIS-/i, `${BRAND_SHORT}-`);
}

export function formatDateTimeAr(value?: string | null): string {
  if (!value) return "غير متاح";
  return new Date(value).toLocaleString("ar-EG");
}

export function formatPlateSummary(plate?: Pick<CasePlateRead, "display_summary_ar" | "letters_ar" | "digits_ar" | "arabic_text_display"> | null): string {
  if (!plate) return "بدون لوحة مؤكدة";
  const compact = [plate.display_summary_ar, `${plate.letters_ar} ${plate.digits_ar}`.trim(), plate.arabic_text_display].find(
    (value) => Boolean(value && value.trim()),
  );
  return compact?.trim() || "بدون لوحة مؤكدة";
}

export function formatViolationSummary(item: Pick<CaseListItem, "violation_summary_ar" | "violations">): string {
  if (item.violation_summary_ar?.trim()) return item.violation_summary_ar.trim();
  const violations = Array.isArray(item.violations) ? item.violations : [];
  const names = Array.from(
    new Set(
      violations
        .filter((violation) => violation.actionable)
        .map((violation) => violation.display_name_ar)
        .filter(Boolean),
    ),
  );
  return names.join("، ") || "لا توجد مخالفة مؤكدة";
}

export function translateReviewFlag(flag: string, violations: CaseViolation[] = []): string {
  if (FLAG_LABELS[flag]) return FLAG_LABELS[flag];

  if (flag.startsWith("association:")) {
    return translateAssociationStatus(flag.split(":")[1]);
  }

  if (flag.startsWith("doubtful_violation:")) {
    const code = flag.split(":")[1] ?? "";
    return `ثقة المخالفة منخفضة: ${resolveViolationName(code, violations)}`;
  }

  if (flag.startsWith("review_violation:")) {
    const code = flag.split(":")[1] ?? "";
    return `المخالفة تحتاج مراجعة: ${resolveViolationName(code, violations)}`;
  }

  return humanizeLabel(flag);
}

function resolveViolationName(code: string, violations: CaseViolation[]): string {
  const safeViolations = Array.isArray(violations) ? violations : [];
  return safeViolations.find((item) => item.code === code)?.display_name_ar ?? violationLabelFromCode(code);
}

export function summarizeReviewFlags(flags: string[] = [], violations: CaseViolation[] = []): string[] {
  if (!Array.isArray(flags) || flags.length === 0) return [];
  return Array.from(new Set(flags.map((flag) => translateReviewFlag(flag, violations))));
}

export function plateReadinessLabel(plate?: Pick<CasePlateRead, "is_confident"> | null): string {
  if (!plate) return "بدون قراءة مؤكدة";
  return plate.is_confident ? "قراءة مؤكدة" : "قراءة تحتاج مراجعة";
}

export function getHighlightedViolation(detail: Pick<CaseDetail, "highlighted_violation_code" | "violations">): string {
  if (!detail.highlighted_violation_code) return "لا توجد مخالفة رئيسية";
  return resolveViolationName(detail.highlighted_violation_code, Array.isArray(detail.violations) ? detail.violations : []);
}
