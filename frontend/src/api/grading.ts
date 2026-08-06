// * ==============================================================================
// *                          API: Grading
// * ==============================================================================
// ? منطبق با app/routers/grading.py
// ! grade و gradeAll واقعاً تصحیح را (دوباره) اجرا می‌کنند - فقط از دکمه
// ! "تصحیح" صدا زده شوند. getResults فقط می‌خواند و هرگز تصحیح نمی‌کند - این
// ! برای صفحه "نمایش نتیجه" استفاده می‌شود (طبق قانون صریح پروژه).

import { apiRequest } from "./client";
import type { ExamScoreSummary, GradeResult } from "@/types/domain";

export const gradingApi = {
  gradeSingleSheet: (examId: string, studentId: string) =>
    apiRequest<GradeResult[]>(`/exams/${examId}/students/${studentId}/grade`, {
      method: "POST",
    }),

  gradeAllSheets: (examId: string) =>
    apiRequest<Record<string, GradeResult[]>>(`/exams/${examId}/grade`, {
      method: "POST",
    }),

  getStudentResults: (examId: string, studentId: string) =>
    apiRequest<GradeResult[]>(`/exams/${examId}/students/${studentId}/results`),

  getExamResults: (examId: string) =>
    apiRequest<ExamScoreSummary[]>(`/exams/${examId}/results`),
};
