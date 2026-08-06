// * ==============================================================================
// *                          API: Sheets (Answers)
// * ==============================================================================
// ? منطبق با app/routers/sheets.py

import { apiRequest } from "./client";
import type { SheetStatus, StudentAnswer } from "@/types/domain";
import type { SheetSubmitRequest } from "@/types/requests";

export const sheetsApi = {
  submitAnswers: (examId: string, studentId: string, payload: SheetSubmitRequest) =>
    apiRequest<StudentAnswer[]>(`/exams/${examId}/students/${studentId}/answers`, {
      method: "POST",
      body: payload,
    }),

  getAnswers: (examId: string, studentId: string) =>
    apiRequest<StudentAnswer[]>(`/exams/${examId}/students/${studentId}/answers`),

  listStatuses: (examId: string) =>
    apiRequest<SheetStatus[]>(`/exams/${examId}/sheets`),
};
