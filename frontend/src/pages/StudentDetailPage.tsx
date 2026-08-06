// * ==============================================================================
// *                          StudentDetailPage
// * ==============================================================================
// ? Endpoint ها: GET /students/{id}, GET /students/{id}/analytics,
// ? GET /students/{id}/analytics/compare/{examId} (فقط با انتخاب آزمون)،
// ? GET /classes/{id} (فقط برای نمایش نام کلاس)
// ! تمام محاسبات (میانگین، روند، تفکیک موضوعی، مقایسه) از Backend می‌آیند -
// ? اینجا فقط نمایش داده می‌شوند، دوباره محاسبه نمی‌شوند.

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { TrendBadge } from "@/components/common/StatusBadges";
import { useClass } from "@/hooks/useClasses";
import { useStudent } from "@/hooks/useStudents";
import { useClassComparison, useStudentAnalytics } from "@/hooks/useAnalytics";

export function StudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const { data: student, isLoading: studentLoading, isError, error } = useStudent(studentId);
  const { data: analytics, isLoading: analyticsLoading } = useStudentAnalytics(studentId);
  const { data: schoolClass } = useClass(student?.class_id ?? undefined);
  const [compareExamId, setCompareExamId] = useState<string | undefined>(undefined);
  const { data: comparison } = useClassComparison(studentId, compareExamId);

  if (studentLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!student) return null;

  const topicEntries = analytics ? Object.entries(analytics.topic_breakdown) : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={student.full_name}
        description={[student.student_code, schoolClass?.name].filter(Boolean).join(" · ") || undefined}
      />

      {analyticsLoading && <LoadingState />}

      {analytics && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">میانگین کلی</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{analytics.overall_average_percentage}٪</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">تعداد آزمون‌ها</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{analytics.exam_history.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">روند عملکرد</CardTitle>
              </CardHeader>
              <CardContent>
                <TrendBadge trend={analytics.trend} />
              </CardContent>
            </Card>
          </div>

          {/* * تاریخچه آزمون‌ها */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">تاریخچه آزمون‌ها</CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.exam_history.length === 0 ? (
                <EmptyState title="هنوز نتیجه‌ای برای این دانش‌آموز ثبت نشده" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>آزمون</TableHead>
                      <TableHead>نمره</TableHead>
                      <TableHead>درصد</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {analytics.exam_history.map((entry) => (
                      <TableRow key={entry.exam_id}>
                        <TableCell className="font-medium">{entry.exam_title}</TableCell>
                        <TableCell>
                          {entry.total_score} از {entry.max_total_score}
                        </TableCell>
                        <TableCell>
                          <Badge variant={entry.percentage >= 50 ? "success" : "warning"}>
                            {entry.percentage}٪
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Link
                            to={`/exams/${entry.exam_id}/students/${studentId}/result`}
                            className="text-sm text-primary hover:underline"
                          >
                            مشاهده جزئیات
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* * نقاط قوت/ضعف موضوعی */}
          {topicEntries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">تحلیل موضوعی (نقاط قوت و ضعف)</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topicEntries.map(([topic, percentage]) => ({ topic, percentage }))}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis dataKey="topic" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <Bar dataKey="percentage" radius={[4, 4, 0, 0]} className="fill-primary" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* * مقایسه با میانگین کلاس */}
          {analytics.exam_history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">مقایسه با میانگین کلاس</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="max-w-xs">
                  <Select value={compareExamId} onValueChange={setCompareExamId}>
                    <SelectTrigger>
                      <SelectValue placeholder="یک آزمون را انتخاب کنید" />
                    </SelectTrigger>
                    <SelectContent>
                      {analytics.exam_history.map((entry) => (
                        <SelectItem key={entry.exam_id} value={entry.exam_id}>
                          {entry.exam_title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {comparison && (
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-xs text-muted-foreground">نمره دانش‌آموز</p>
                      <p className="mt-1 text-2xl font-bold">{comparison.student_percentage}٪</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">میانگین کلاس</p>
                      <p className="mt-1 text-2xl font-bold">{comparison.class_average_percentage}٪</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">اختلاف</p>
                      <p
                        className={
                          comparison.difference >= 0
                            ? "mt-1 text-2xl font-bold text-success"
                            : "mt-1 text-2xl font-bold text-destructive"
                        }
                      >
                        {comparison.difference > 0 ? "+" : ""}
                        {comparison.difference}٪
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
