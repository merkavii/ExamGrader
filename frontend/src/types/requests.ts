// * ==============================================================================
// *                       API Request Payload Types
// * ==============================================================================
// ? آینه app/schemas.py - این‌ها بدنه درخواست‌هایی هستند که معلم پر می‌کند؛
// ? فیلدهایی مثل id که سرور خودش می‌سازد، اینجا وجود ندارند (دقیقاً مثل
// ? تصمیم معماری Backend که ExamCreateRequest را از خود Exam جدا نگه داشت).

import type {
  AnswerContent,
  AnswerSource,
  CorrectAnswer,
  QuestionType,
  Rubric,
} from "./domain";

export interface ExamCreateRequest {
  title: string;
}

export interface QuestionCreateRequest {
  question_text: string;
  question_type: QuestionType;
  correct_answer: CorrectAnswer;
  max_score: number;
  numeric_tolerance?: number | null;
  rubric?: Rubric | null;
  options?: string[] | null;
  topic?: string | null;
}

export interface SchoolClassCreateRequest {
  name: string;
  academic_year?: string | null;
}

export interface StudentCreateRequest {
  full_name: string;
  student_code?: string | null;
  class_id?: string | null;
}

export interface StudentAnswerSubmitItem {
  question_id: string;
  answer_content: AnswerContent;
}

export interface SheetSubmitRequest {
  answers: StudentAnswerSubmitItem[];
  source?: AnswerSource;
}

export interface TeacherOverrideRequest {
  final_score: number;
  teacher_reasoning: string;
}
