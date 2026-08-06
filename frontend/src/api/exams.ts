// * ==============================================================================
// *                          API: Exams / Questions
// * ==============================================================================
// ? منطبق با app/routers/exams.py

import { apiRequest } from "./client";
import type { Exam, Question } from "@/types/domain";
import type { ExamCreateRequest, QuestionCreateRequest } from "@/types/requests";

export const examsApi = {
  list: () => apiRequest<Exam[]>("/exams"),

  get: (examId: string) => apiRequest<Exam>(`/exams/${examId}`),

  create: (payload: ExamCreateRequest) =>
    apiRequest<Exam>("/exams", { method: "POST", body: payload }),

  listQuestions: (examId: string) =>
    apiRequest<Question[]>(`/exams/${examId}/questions`),

  addQuestion: (examId: string, payload: QuestionCreateRequest) =>
    apiRequest<Question>(`/exams/${examId}/questions`, {
      method: "POST",
      body: payload,
    }),
};
