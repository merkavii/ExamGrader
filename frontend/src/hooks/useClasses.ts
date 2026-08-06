// * ==============================================================================
// *                          Hooks: Classes
// * ==============================================================================
// ? هر Hook فقط api/classes.ts را با TanStack Query بسته‌بندی می‌کند - هیچ
// ? منطق تجاری (محاسبه/تصمیم) اینجا نیست، فقط کش و وضعیت درخواست.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { classesApi } from "@/api/classes";
import type { SchoolClassCreateRequest } from "@/types/requests";

export function useClasses() {
  return useQuery({ queryKey: ["classes"], queryFn: classesApi.list });
}

export function useClass(classId: string | undefined) {
  return useQuery({
    queryKey: ["classes", classId],
    queryFn: () => classesApi.get(classId!),
    enabled: !!classId,
  });
}

export function useClassStudents(classId: string | undefined) {
  return useQuery({
    queryKey: ["classes", classId, "students"],
    queryFn: () => classesApi.listStudents(classId!),
    enabled: !!classId,
  });
}

export function useCreateClass() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SchoolClassCreateRequest) => classesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
  });
}
