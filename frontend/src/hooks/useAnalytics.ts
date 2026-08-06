// * ==============================================================================
// *                          Hooks: Analytics
// * ==============================================================================

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/api/analytics";

export function useExamAnalytics(examId: string | undefined) {
  return useQuery({
    queryKey: ["analytics", "exam", examId],
    queryFn: () => analyticsApi.getExamAnalytics(examId!),
    enabled: !!examId,
  });
}

export function useStudentAnalytics(studentId: string | undefined) {
  return useQuery({
    queryKey: ["analytics", "student", studentId],
    queryFn: () => analyticsApi.getStudentAnalytics(studentId!),
    enabled: !!studentId,
  });
}

export function useClassComparison(studentId: string | undefined, examId: string | undefined) {
  return useQuery({
    queryKey: ["analytics", "compare", studentId, examId],
    queryFn: () => analyticsApi.compareToClass(studentId!, examId!),
    enabled: !!studentId && !!examId,
  });
}
