// * ==============================================================================
// *                          Hook: Dashboard Stats
// * ==============================================================================
// ? هیچ Endpoint اختصاصی "آمار کلی سامانه" در Backend وجود ندارد - این هوک
// ? فقط چند Endpoint واقعی موجود را با هم ترکیب می‌کند (شمارش طول آرایه‌های
// ? واقعی)، نه این‌که آماری را حدس بزند یا خودش محاسبه‌ای بسازد.
// ?
// ! محدودیت شناخته‌شده: برای "تعداد کارنامه‌های تصحیح‌شده"، چون Backend یک
// ! Endpoint سراسری برای این آمار ندارد، این هوک به‌ازای هر آزمون یک‌بار
// ! GET /exams/{id}/results می‌زند و طول آرایه‌ها را جمع می‌زند. برای تعداد کم
// ! آزمون (مقیاس دمو) مشکلی ندارد؛ برای مقیاس واقعی، افزودن یک Endpoint آماری
// ! اختصاصی در Backend پیشنهاد بهتری است.

import { useQuery } from "@tanstack/react-query";
import { classesApi } from "@/api/classes";
import { examsApi } from "@/api/exams";
import { gradingApi } from "@/api/grading";
import { reviewApi } from "@/api/review";
import { studentsApi } from "@/api/students";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const [classes, students, exams, reviewQueue] = await Promise.all([
        classesApi.list(),
        studentsApi.list(),
        examsApi.list(),
        reviewApi.list(),
      ]);

      const resultsPerExam = await Promise.all(
        exams.map((exam) => gradingApi.getExamResults(exam.id))
      );
      const gradedSheetCount = resultsPerExam.reduce((sum, r) => sum + r.length, 0);

      return {
        classCount: classes.length,
        studentCount: students.length,
        examCount: exams.length,
        needsReviewCount: reviewQueue.length,
        gradedSheetCount,
      };
    },
  });
}
