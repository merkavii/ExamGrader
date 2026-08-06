// * ==============================================================================
// *                          API: Review Queue
// * ==============================================================================
// ? منطبق با app/routers/review.py

import { apiRequest } from "./client";
import type { GradeResult, ReviewQueueItem } from "@/types/domain";
import type { TeacherOverrideRequest } from "@/types/requests";

export const reviewApi = {
  list: (examId?: string) =>
    apiRequest<ReviewQueueItem[]>("/review-queue", { params: { exam_id: examId } }),

  override: (gradeResultId: string, payload: TeacherOverrideRequest) =>
    apiRequest<GradeResult>(`/review-queue/${gradeResultId}/override`, {
      method: "POST",
      body: payload,
    }),
};
