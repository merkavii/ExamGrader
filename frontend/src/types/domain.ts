// * ==============================================================================
// *                          Domain Types
// * ==============================================================================
// ? این فایل آینه دقیق مدل‌های Pydantic در Backend است - domain/models/*.py و
// ? grading/aggregator.py و analytics/*.py. هیچ فیلدی اینجا حدس زده نشده؛
// ? هرکدام مستقیماً از خواندن کد واقعی Backend استخراج شده‌اند.
//
// ! اگر Backend فیلدی اضافه/حذف کرد، این فایل باید دستی هماهنگ شود - این
// ! پروژه از تولید خودکار Type از OpenAPI استفاده نمی‌کند (تا وابستگی اضافه
// ! نشود)، پس این‌جا تنها منبع حقیقت سمت Frontend برای شکل داده‌هاست.

// * --------------------------- Enums (domain/models/enums.py) ---------------------------

export type QuestionType =
  | "multiple_choice"
  | "true_false"
  | "short_answer"
  | "fill_in_blank"
  | "numeric"
  | "matching"
  | "essay";

// ? فقط این ۵ نوع در Backend فعلی واقعاً Grader دارند (grading/orchestrator.py).
// ? matching و fill_in_blank در enum هست ولی هیچ Grader ای برایشان ثبت نشده -
// ? پس در فرم ساخت سؤال نباید انتخاب‌پذیر باشند.
export const GRADABLE_QUESTION_TYPES: QuestionType[] = [
  "multiple_choice",
  "true_false",
  "numeric",
  "short_answer",
  "essay",
];

export type AnswerSource = "manual" | "image" | "pdf" | "excel" | "api";

export type GradingStatus = "not_graded" | "graded" | "needs_review" | "teacher_overridden";

export type GradingMethod = "rule_based" | "llm" | "teacher";

// * ------------------------------------ Exam ------------------------------------

export interface CorrectAnswer {
  selected_option?: string | null;
  text?: string | null;
  numeric_value?: number | null;
  matching_pairs?: Record<string, string> | null;
  essay_reference?: string | null;
}

export interface RubricCriterion {
  description: string;
  points: number;
}

export interface Rubric {
  criteria: RubricCriterion[];
}

export interface Question {
  id: string;
  exam_id: string;
  question_text: string;
  question_type: QuestionType;
  correct_answer: CorrectAnswer;
  max_score: number;
  numeric_tolerance?: number | null;
  rubric?: Rubric | null;
  options?: string[] | null;
  topic?: string | null;
}

export interface Exam {
  id: string;
  title: string;
  questions: Question[];
  created_at: string;
}

// * ---------------------------------- Student / Class ----------------------------------

export interface SchoolClass {
  id: string;
  name: string;
  academic_year?: string | null;
}

export interface Student {
  id: string;
  full_name: string;
  student_code?: string | null;
  class_id?: string | null;
}

export interface AnswerContent {
  selected_option?: string | null;
  text?: string | null;
  numeric_value?: number | null;
  matching_pairs?: Record<string, string> | null;
}

export interface StudentAnswer {
  id: string;
  exam_id: string;
  student_id: string;
  question_id: string;
  answer_content: AnswerContent;
  source: AnswerSource;
  extraction_confidence?: number | null;
}

export interface SheetStatus {
  student_id: string;
  student_full_name: string;
  answered_questions: number;
  total_questions: number;
}

// * ---------------------------------- Grading ----------------------------------

export interface ConfidenceScore {
  image_quality?: number | null;
  extraction_confidence?: number | null;
  grading_confidence: number;
  final_score: number;
}

export interface GradeResult {
  id: string;
  question_id: string;
  student_id: string;
  exam_id: string;
  score: number;
  max_score: number;
  reasoning: string;
  confidence: ConfidenceScore;
  status: GradingStatus;
  grading_method: GradingMethod;
  graded_by: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ExamScoreSummary {
  student_id: string;
  exam_id: string;
  total_score: number;
  max_total_score: number;
  percentage: number;
  graded_question_count: number;
  needs_review_question_count: number;
}

export interface ReviewQueueItem {
  grade_result: GradeResult;
  student_full_name: string;
  student_code?: string | null;
  exam_title: string;
  question_text: string;
  question_topic?: string | null;
}

// * ---------------------------------- Analytics ----------------------------------

export interface QuestionAnalytics {
  question_id: string;
  question_text: string;
  topic?: string | null;
  participant_count: number;
  correct_percentage: number;
  average_score_ratio: number;
}

export interface ExamClassAnalytics {
  exam_id: string;
  participant_count: number;
  average_score: number;
  average_percentage: number;
  highest_score: number;
  lowest_score: number;
  score_distribution: number[];
  question_analytics: QuestionAnalytics[];
  topic_breakdown: Record<string, number>;
}

export interface ExamHistoryEntry {
  exam_id: string;
  exam_title: string;
  total_score: number;
  max_total_score: number;
  percentage: number;
}

export type StudentTrend = "improving" | "declining" | "stable" | "insufficient_data";

export interface StudentAnalytics {
  student_id: string;
  exam_history: ExamHistoryEntry[];
  overall_average_percentage: number;
  topic_breakdown: Record<string, number>;
  trend: StudentTrend;
}

export interface ClassComparison {
  exam_id: string;
  student_percentage: number;
  class_average_percentage: number;
  difference: number;
}
