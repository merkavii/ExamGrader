// * ==============================================================================
// *                            GradeResultPage
// * ==============================================================================
// ? Endpoint ها: GET /exams/{id}/students/{id}/results (فقط خواندن، بدون تصحیح
// ? مجدد) + GET /exams/{id} (متن سؤال/پاسخ صحیح) + GET /exams/{id}/students/{id}/answers
// ? (پاسخ واقعی دانش‌آموز) + GET /exams/{id}/results (نمره کل - از Backend
// ? خوانده می‌شود، در Frontend دوباره جمع زده نمی‌شود).
//
// ! این صفحه هرگز POST .../grade را صدا نمی‌زند - طبق قانون صریح پروژه.

import { Link, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { GradingMethodBadge, GradingStatusBadge } from "@/components/common/StatusBadges";
import { useExam } from "@/hooks/useExams";
import { useStudent } from "@/hooks/useStudents";
import { useStudentAnswers } from "@/hooks/useSheets";
import { useExamResults, useStudentResults } from "@/hooks/useGrading";
import { formatAnswerContent } from "@/lib/formatAnswer";

export function GradeResultPage() {
  const { examId, studentId } = useParams<{ examId: string; studentId: string }>();
  const { data: results, isLoading, isError, error } = useStudentResults(examId, studentId);
  const { data: exam } = useExam(examId);
  const { data: student } = useStudent(studentId);
  const { data: answers } = useStudentAnswers(examId, studentId);
  const { data: examResults } = useExamResults(examId);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;

  if (!results || results.length === 0) {
    return (
      <EmptyState
        title="هنوز نتیجه‌ای برای این دانش‌آموز ثبت نشده"
        description="ابتدا از صفحه آزمون، این برگه را تصحیح کنید."
        action={
          examId && (
            <Button asChild variant="outline">
              <Link to={`/exams/${examId}`}>بازگشت به آزمون</Link>
            </Button>
          )
        }
      />
    );
  }

  // ? نمره کل از همان Endpoint محاسبه‌شده Backend خوانده می‌شود - نه با جمع
  // ? دستی نمرات در همین‌جا.
  const summary = examResults?.find((s) => s.student_id === studentId);
  const answerByQuestion = new Map(answers?.map((a) => [a.question_id, a]));
  const questionById = new Map(exam?.questions.map((q) => [q.id, q]));

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title={`نتیجه تصحیح - ${student?.full_name ?? ""}`}
        description={exam?.title}
      />

      {summary && (
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">نمره نهایی</p>
              <p className="text-3xl font-bold">
                {summary.total_score} از {summary.max_total_score}
              </p>
            </div>
            <Badge variant={summary.percentage >= 50 ? "success" : "warning"} className="text-base">
              {summary.percentage}٪
            </Badge>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {results.map((result) => {
          const question = questionById.get(result.question_id);
          const studentAnswer = answerByQuestion.get(result.question_id);
          return (
            <Card key={result.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4 pb-2">
                <CardTitle className="text-sm font-medium">
                  {question?.question_text ?? "سؤال"}
                </CardTitle>
                <div className="flex shrink-0 gap-2">
                  <GradingStatusBadge status={result.status} />
                  <GradingMethodBadge method={result.grading_method} />
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-xs text-muted-foreground">پاسخ دانش‌آموز</p>
                    <p className="mt-0.5">
                      {studentAnswer ? formatAnswerContent(studentAnswer.answer_content) : "—"}
                    </p>
                  </div>
                  {question && (
                    <div>
                      <p className="text-xs text-muted-foreground">پاسخ صحیح</p>
                      <p className="mt-0.5">{formatAnswerContent(question.correct_answer)}</p>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-xs text-muted-foreground">دلیل نمره‌دهی</p>
                  <p className="mt-0.5">{result.reasoning}</p>
                </div>

                <div className="flex items-center justify-between border-t pt-3">
                  <span className="text-xs text-muted-foreground">
                    اطمینان تصحیح: {result.confidence.final_score}٪
                  </span>
                  <span className="font-semibold">
                    {result.score} از {result.max_score}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
