// * ==============================================================================
// *                            ExamDetailPage
// * ==============================================================================
// ? Endpoint ها به تفکیک تب:
// ?   سؤالات   -> GET /exams/{id} (شامل questions تو در تو)
// ?   برگه‌ها   -> GET /exams/{id}/sheets ، POST /exams/{id}/students/{id}/grade
// ?   نتایج    -> GET /exams/{id}/results ، POST /exams/{id}/grade
// ?   تحلیل    -> GET /exams/{id}/analytics

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { questionTypeLabel } from "@/components/common/StatusBadges";
import { useExam } from "@/hooks/useExams";
import { useSheetStatuses } from "@/hooks/useSheets";
import { useExamResults, useGradeAllSheets, useGradeSingleSheet } from "@/hooks/useGrading";
import { useExamAnalytics } from "@/hooks/useAnalytics";

export function ExamDetailPage() {
  const { examId } = useParams<{ examId: string }>();
  const { data: exam, isLoading, isError, error } = useExam(examId);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!exam || !examId) return null;

  return (
    <div>
      <PageHeader title={exam.title} description={`${exam.questions.length} سؤال`} />

      <Tabs defaultValue="questions">
        <TabsList>
          <TabsTrigger value="questions">سؤال‌ها</TabsTrigger>
          <TabsTrigger value="sheets">برگه‌ها</TabsTrigger>
          <TabsTrigger value="results">نتایج</TabsTrigger>
          <TabsTrigger value="analytics">تحلیل آزمون</TabsTrigger>
        </TabsList>

        <TabsContent value="questions">
          <QuestionsTab questions={exam.questions} />
        </TabsContent>
        <TabsContent value="sheets">
          <SheetsTab examId={examId} />
        </TabsContent>
        <TabsContent value="results">
          <ResultsTab examId={examId} />
        </TabsContent>
        <TabsContent value="analytics">
          <AnalyticsTab examId={examId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// * --------------------------------- تب سؤال‌ها ---------------------------------

function QuestionsTab({ questions }: { questions: import("@/types/domain").Question[] }) {
  if (questions.length === 0) {
    return <EmptyState title="هنوز سؤالی به این آزمون اضافه نشده" />;
  }
  return (
    <div className="space-y-3">
      {questions.map((question, index) => (
        <Card key={question.id}>
          <CardContent className="flex items-start justify-between gap-4 p-4">
            <div className="min-w-0 flex-1">
              <p className="font-medium">
                {index + 1}. {question.question_text}
              </p>
              {question.options && (
                <p className="mt-1 text-sm text-muted-foreground">
                  گزینه‌ها: {question.options.join("، ")}
                </p>
              )}
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <Badge variant="outline">{questionTypeLabel(question.question_type)}</Badge>
              <Badge variant="secondary">{question.max_score} نمره</Badge>
              {question.topic && <Badge variant="success">{question.topic}</Badge>}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// * ---------------------------------- تب برگه‌ها ----------------------------------

function SheetsTab({ examId }: { examId: string }) {
  const { data: sheets, isLoading, isError, error } = useSheetStatuses(examId);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!sheets || sheets.length === 0) {
    return (
      <EmptyState
        title="هنوز هیچ دانش‌آموزی برای این آزمون پاسخ ثبت نکرده"
        description="از صفحه دانش‌آموزان، پاسخ یک دانش‌آموز را برای این آزمون ثبت کنید."
      />
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>دانش‌آموز</TableHead>
            <TableHead>وضعیت پاسخ‌ها</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {sheets.map((sheet) => (
            <SheetRow key={sheet.student_id} examId={examId} sheet={sheet} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function SheetRow({
  examId,
  sheet,
}: {
  examId: string;
  sheet: import("@/types/domain").SheetStatus;
}) {
  const gradeSheet = useGradeSingleSheet(examId, sheet.student_id);
  const isComplete = sheet.answered_questions === sheet.total_questions;

  const handleGrade = () => {
    gradeSheet.mutate(undefined, {
      onSuccess: () => toast.success(`برگه ${sheet.student_full_name} تصحیح شد`),
      onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در تصحیح"),
    });
  };

  return (
    <TableRow>
      <TableCell className="font-medium">{sheet.student_full_name}</TableCell>
      <TableCell>
        <Badge variant={isComplete ? "success" : "warning"}>
          {sheet.answered_questions} از {sheet.total_questions} پاسخ ثبت شده
        </Badge>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link to={`/exams/${examId}/students/${sheet.student_id}/answer`}>ثبت/ویرایش پاسخ</Link>
          </Button>
          {/* ! غیرفعال هنگام اجرا - جلوگیری از چند بار کلیک (طبق قانون پروژه) */}
          <Button size="sm" onClick={handleGrade} disabled={gradeSheet.isPending}>
            {gradeSheet.isPending ? "در حال تصحیح..." : "تصحیح این برگه"}
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link to={`/exams/${examId}/students/${sheet.student_id}/result`}>مشاهده نتیجه</Link>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}

// * ---------------------------------- تب نتایج ----------------------------------

function ResultsTab({ examId }: { examId: string }) {
  const { data: results, isLoading, isError, error } = useExamResults(examId);
  const gradeAll = useGradeAllSheets(examId);

  const handleGradeAll = () => {
    gradeAll.mutate(undefined, {
      onSuccess: (data) => toast.success(`تصحیح ${Object.keys(data).length} برگه با موفقیت انجام شد`),
      onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در تصحیح دسته‌ای"),
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        {/* ! غیرفعال هنگام اجرا - جلوگیری از چند بار کلیک روی «تصحیح همه» */}
        <Button onClick={handleGradeAll} disabled={gradeAll.isPending}>
          {gradeAll.isPending ? "در حال تصحیح همه برگه‌ها..." : "تصحیح همه برگه‌ها"}
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {results && results.length === 0 && (
        <EmptyState
          title="هنوز نتیجه‌ای ثبت نشده"
          description="روی «تصحیح همه برگه‌ها» بزنید یا از تب برگه‌ها یک‌به‌یک تصحیح کنید."
        />
      )}

      {results && results.length > 0 && (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>دانش‌آموز</TableHead>
                <TableHead>نمره</TableHead>
                <TableHead>درصد</TableHead>
                <TableHead>نیازمند بازبینی</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((summary) => (
                <ResultRow key={summary.student_id} examId={examId} summary={summary} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function ResultRow({
  examId,
  summary,
}: {
  examId: string;
  summary: import("@/types/domain").ExamScoreSummary;
}) {
  // ? نام دانش‌آموز در ExamScoreSummary نیست - از GET /exams/{id}/sheets که قبلاً
  // ? واکشی شده می‌خوانیم تا درخواست تکراری نزنیم.
  const { data: sheets } = useSheetStatuses(examId);
  const studentName =
    sheets?.find((s) => s.student_id === summary.student_id)?.student_full_name ?? summary.student_id;

  return (
    <TableRow>
      <TableCell className="font-medium">{studentName}</TableCell>
      <TableCell>
        {summary.total_score} از {summary.max_total_score}
      </TableCell>
      <TableCell>
        <Badge variant={summary.percentage >= 50 ? "success" : "warning"}>{summary.percentage}٪</Badge>
      </TableCell>
      <TableCell>
        {summary.needs_review_question_count > 0 ? (
          <Badge variant="warning">{summary.needs_review_question_count} مورد</Badge>
        ) : (
          "—"
        )}
      </TableCell>
      <TableCell>
        <Link
          to={`/exams/${examId}/students/${summary.student_id}/result`}
          className="text-sm text-primary hover:underline"
        >
          مشاهده جزئیات
        </Link>
      </TableCell>
    </TableRow>
  );
}

// * --------------------------------- تب تحلیل آزمون ---------------------------------

function AnalyticsTab({ examId }: { examId: string }) {
  const { data: analytics, isLoading, isError, error } = useExamAnalytics(examId);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!analytics) return null;

  if (analytics.participant_count === 0) {
    return <EmptyState title="هنوز داده‌ای برای تحلیل وجود ندارد" description="ابتدا حداقل یک برگه را تصحیح کنید." />;
  }

  const topicEntries = Object.entries(analytics.topic_breakdown);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatBox label="شرکت‌کننده" value={analytics.participant_count} />
        <StatBox label="میانگین درصد" value={`${analytics.average_percentage}٪`} />
        <StatBox label="بیشترین نمره" value={analytics.highest_score} />
        <StatBox label="کمترین نمره" value={analytics.lowest_score} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">سؤال‌های سخت (کمترین درصد پاسخ صحیح)</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analytics.question_analytics.slice(0, 6)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="question_text"
                width={160}
                tick={{ fontSize: 11 }}
                tickFormatter={(value: string) => (value.length > 22 ? value.slice(0, 22) + "…" : value)}
              />
              <Tooltip formatter={(value: number) => `${value}٪`} />
              <Bar dataKey="correct_percentage" radius={[0, 4, 4, 0]} className="fill-primary" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {topicEntries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">تحلیل موضوعی کلاس</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicEntries.map(([topic, percentage]) => ({ topic, percentage }))}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="topic" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value: number) => `${value}٪`} />
                <Bar dataKey="percentage" radius={[4, 4, 0, 0]} className="fill-success" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
