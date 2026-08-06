// * ==============================================================================
// *                          Hooks: Students
// * ==============================================================================

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { studentsApi } from "@/api/students";
import type { StudentCreateRequest } from "@/types/requests";

export function useStudents() {
  return useQuery({ queryKey: ["students"], queryFn: studentsApi.list });
}

export function useStudent(studentId: string | undefined) {
  return useQuery({
    queryKey: ["students", studentId],
    queryFn: () => studentsApi.get(studentId!),
    enabled: !!studentId,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentCreateRequest) => studentsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      // ? اگر دانش‌آموز به کلاسی وصل شده، لیست آن کلاس هم تازه شود
      queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
  });
}
