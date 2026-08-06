// * ==============================================================================
// *                          Hooks: Grading
// * ==============================================================================
// ? هوک‌های تصحیح (POST) با هوک‌های مشاهده نتیجه (GET، بدون تصحیح مجدد) عمداً
// ? جدا هستند - همان تفکیک معماری‌ای که در Backend بین grade_single_sheet و
// ? get_student_results وجود دارد.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { gradingApi } from "@/api/grading";

export function useGradeSingleSheet(examId: string, studentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => gradingApi.gradeSingleSheet(examId, studentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["exams", examId, "students", studentId, "results"],
      });
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "results"] });
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "sheets"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "analytics"] });
    },
  });
}

export function useGradeAllSheets(examId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => gradingApi.gradeAllSheets(examId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "results"] });
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "sheets"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["exams", examId, "analytics"] });
    },
  });
}

export function useStudentResults(examId: string | undefined, studentId: string | undefined) {
  return useQuery({
    queryKey: ["exams", examId, "students", studentId, "results"],
    queryFn: () => gradingApi.getStudentResults(examId!, studentId!),
    enabled: !!examId && !!studentId,
  });
}

export function useExamResults(examId: string | undefined) {
  return useQuery({
    queryKey: ["exams", examId, "results"],
    queryFn: () => gradingApi.getExamResults(examId!),
    enabled: !!examId,
  });
}
