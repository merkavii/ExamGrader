// * ==============================================================================
// *              Badge های اختصاصی برای وضعیت/روش تصحیح
// * ==============================================================================
// ? این‌ها فقط نمایش‌دهنده هستند - مقدار status/grading_method مستقیماً از
// ? GradeResult واقعی Backend می‌آید، اینجا هیچ منطقی برای "تصمیم‌گیری" وضعیت
// ? نیست (طبق قانون: منطق تصحیح در Frontend تکرار نشود).

import { Badge } from "@/components/ui/badge";
import type { GradingMethod, GradingStatus } from "@/types/domain";

const STATUS_LABELS: Record<GradingStatus, { label: string; variant: "success" | "warning" | "secondary" | "outline" }> = {
  graded: { label: "تصحیح‌شده", variant: "success" },
  needs_review: { label: "نیازمند بازبینی", variant: "warning" },
  teacher_overridden: { label: "اصلاح‌شده توسط معلم", variant: "secondary" },
  not_graded: { label: "تصحیح‌نشده", variant: "outline" },
};

export function GradingStatusBadge({ status }: { status: GradingStatus }) {
  const config = STATUS_LABELS[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

const METHOD_LABELS: Record<GradingMethod, string> = {
  rule_based: "قانون‌محور",
  llm: "هوش مصنوعی",
  teacher: "معلم",
};

export function GradingMethodBadge({ method }: { method: GradingMethod }) {
  return <Badge variant="outline">{METHOD_LABELS[method]}</Badge>;
}

const QUESTION_TYPE_LABELS: Record<string, string> = {
  multiple_choice: "چهارگزینه‌ای",
  true_false: "درست/غلط",
  short_answer: "پاسخ کوتاه",
  fill_in_blank: "جای خالی",
  numeric: "عددی",
  matching: "وصل‌کردنی",
  essay: "تشریحی",
};

export function questionTypeLabel(type: string): string {
  return QUESTION_TYPE_LABELS[type] ?? type;
}

const TREND_LABELS: Record<string, { label: string; variant: "success" | "warning" | "secondary" | "outline" }> = {
  improving: { label: "روند بهبود", variant: "success" },
  declining: { label: "روند افت", variant: "warning" },
  stable: { label: "روند ثابت", variant: "secondary" },
  insufficient_data: { label: "داده کافی نیست", variant: "outline" },
};

export function TrendBadge({ trend }: { trend: string }) {
  const config = TREND_LABELS[trend] ?? TREND_LABELS.insufficient_data;
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
