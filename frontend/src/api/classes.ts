// * ==============================================================================
// *                          API: Classes
// * ==============================================================================
// ? منطبق با app/routers/classes.py - هر تابع دقیقاً یک Endpoint واقعی است.

import { apiRequest } from "./client";
import type { SchoolClass, Student } from "@/types/domain";
import type { SchoolClassCreateRequest } from "@/types/requests";

export const classesApi = {
  list: () => apiRequest<SchoolClass[]>("/classes"),

  get: (classId: string) => apiRequest<SchoolClass>(`/classes/${classId}`),

  create: (payload: SchoolClassCreateRequest) =>
    apiRequest<SchoolClass>("/classes", { method: "POST", body: payload }),

  listStudents: (classId: string) =>
    apiRequest<Student[]>(`/classes/${classId}/students`),
};
