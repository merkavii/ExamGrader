// * ==============================================================================
// *                          Hooks: Review Queue
// * ==============================================================================

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { reviewApi } from "@/api/review";
import type { TeacherOverrideRequest } from "@/types/requests";

export function useReviewQueue(examId?: string) {
  return useQuery({
    queryKey: ["review-queue", examId],
    queryFn: () => reviewApi.list(examId),
  });
}

export function useOverrideGradeResult() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      gradeResultId,
      payload,
    }: {
      gradeResultId: string;
      payload: TeacherOverrideRequest;
    }) => reviewApi.override(gradeResultId, payload),
    onSuccess: () => {
      // ? بعد از Override، هم صف بازبینی و هم نتایج/تحلیل مرتبط باید تازه شوند
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["exams"] });
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}
