// * ==============================================================================
// *                        formatAnswerContent
// * ==============================================================================
// ? تبدیل AnswerContent/CorrectAnswer (که فقط یکی از فیلدهایش پر است) به یک
// ? رشته قابل نمایش. این فقط قالب‌بندی نمایشی است، نه منطق نمره‌دهی.

import type { AnswerContent, CorrectAnswer } from "@/types/domain";

export function formatAnswerContent(content: AnswerContent | CorrectAnswer): string {
  if (content.selected_option) return content.selected_option === "true"
    ? "درست"
    : content.selected_option === "false"
      ? "غلط"
      : content.selected_option;
  if (content.text) return content.text;
  if (content.numeric_value !== undefined && content.numeric_value !== null) {
    return String(content.numeric_value);
  }
  if ("essay_reference" in content && content.essay_reference) return content.essay_reference;
  if (content.matching_pairs && Object.keys(content.matching_pairs).length > 0) {
    return Object.entries(content.matching_pairs)
      .map(([key, value]) => `${key} → ${value}`)
      .join("، ");
  }
  return "بدون پاسخ";
}
