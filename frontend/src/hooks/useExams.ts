// * ==============================================================================
// *                          Hooks: Exams / Questions
// * ==============================================================================

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { examsApi } from "@/api/exams";
import type { ExamCreateRequest, QuestionCreateRequest } from "@/types/requests";

export function useExams() {
  return useQuery({ queryKey: ["exams"], queryFn: examsApi.list });
}

export function useExam(examId: string | undefined) {
  return useQuery({
    queryKey: ["exams", examId],
    queryFn: () => examsApi.get(examId!),
    enabled: !!examId,
  });
}

export function useCreateExam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExamCreateRequest) => examsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams"] });
    },
  });
}

export function useAddQuestion(examId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: QuestionCreateRequest) => examsApi.addQuestion(examId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams", examId] });
    },
  });
}
