// * ==============================================================================
// *                                  App
// * ==============================================================================
// ? تعریف مسیرها. هر صفحه دقیقاً با یک یا چند Endpoint واقعی Backend کار می‌کند -
// ? جزئیات هر کدام در گزارش پایانی مستند شده.

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { ClassesListPage } from "@/pages/ClassesListPage";
import { ClassDetailPage } from "@/pages/ClassDetailPage";
import { StudentsListPage } from "@/pages/StudentsListPage";
import { StudentDetailPage } from "@/pages/StudentDetailPage";
import { ExamsListPage } from "@/pages/ExamsListPage";
import { ExamCreatePage } from "@/pages/ExamCreatePage";
import { ExamDetailPage } from "@/pages/ExamDetailPage";
import { AnswerEntryPage } from "@/pages/AnswerEntryPage";
import { GradeResultPage } from "@/pages/GradeResultPage";
import { ReviewQueuePage } from "@/pages/ReviewQueuePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export function App() {
  return (
    <BrowserRouter>
      {/* ? Toaster فارسی راست‌چین برای پیام‌های موفقیت/خطای عملیات (بخش ششم) */}
      <Toaster position="top-center" dir="rtl" richColors />
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />

          <Route path="/classes" element={<ClassesListPage />} />
          <Route path="/classes/:classId" element={<ClassDetailPage />} />

          <Route path="/students" element={<StudentsListPage />} />
          <Route path="/students/:studentId" element={<StudentDetailPage />} />

          <Route path="/exams" element={<ExamsListPage />} />
          <Route path="/exams/new" element={<ExamCreatePage />} />
          <Route path="/exams/:examId" element={<ExamDetailPage />} />
          <Route
            path="/exams/:examId/students/:studentId/answer"
            element={<AnswerEntryPage />}
          />
          <Route
            path="/exams/:examId/students/:studentId/result"
            element={<GradeResultPage />}
          />

          <Route path="/review-queue" element={<ReviewQueuePage />} />

          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
