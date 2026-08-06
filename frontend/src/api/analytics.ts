// * ==============================================================================
// *                          API: Analytics
// * ==============================================================================
// ? منطبق با app/routers/analytics.py - همه محاسبات (میانگین، روند، مقایسه)
// ! در Backend انجام شده‌اند؛ این فایل فقط همان نتیجه آماده را می‌گیرد.

import { apiRequest } from "./client";
import type { ClassComparison, ExamClassAnalytics, StudentAnalytics } from "@/types/domain";

export const analyticsApi = {
  getExamAnalytics: (examId: string) =>
    apiRequest<ExamClassAnalytics>(`/exams/${examId}/analytics`),

  getStudentAnalytics: (studentId: string) =>
    apiRequest<StudentAnalytics>(`/students/${studentId}/analytics`),

  compareToClass: (studentId: string, examId: string) =>
    apiRequest<ClassComparison>(`/students/${studentId}/analytics/compare/${examId}`),
};
