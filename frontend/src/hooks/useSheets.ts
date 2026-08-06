// * ==============================================================================
// *                          Hooks: Sheets (Answers)
// * ==============================================================================

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sheetsApi } from "@/api/sheets";
import type { SheetSubmitRequest } from "@/types/requests";

export function useSheetStatuses(examId: string | undefined) {
  return useQuery({
    queryKey: ["exams", examId, "sheets"],
    queryFn: () => sheetsApi.listStatuses(examId!),
    enabled: !!examId,
  });
}

export function useStudentAnswers(examId: string | undefined, studentId: string | undefined) {
  return useQuery({
    queryKey: ["exams", examId, "students", studentId, "answers"],
    queryFn: () => sheetsApi.getAnswers(examId!, studentId!),
    enabled: !!examId && !!studentId,
  });
}

export function useSubmitAnswers(examId: string, studentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SheetSubmitRequest) =>
      sheetsApi.submitAnswers(examId, studentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "sheets"] });
      queryClient.invalidateQueries({
        queryKey: ["exams", examId, "students", studentId, "answers"],
      });
    },
  });
}
