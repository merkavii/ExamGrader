// * ==============================================================================
// *                          API: Students
// * ==============================================================================
// ? منطبق با app/routers/students.py

import { apiRequest } from "./client";
import type { Student } from "@/types/domain";
import type { StudentCreateRequest } from "@/types/requests";

export const studentsApi = {
  list: () => apiRequest<Student[]>("/students"),

  get: (studentId: string) => apiRequest<Student>(`/students/${studentId}`),

  create: (payload: StudentCreateRequest) =>
    apiRequest<Student>("/students", { method: "POST", body: payload }),
};
