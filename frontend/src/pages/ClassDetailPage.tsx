// * ==============================================================================
// *                            ClassDetailPage
// * ==============================================================================
// ? Endpoint ها: GET /classes/{id}, GET /classes/{id}/students

import { Link, useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { useClass, useClassStudents } from "@/hooks/useClasses";

export function ClassDetailPage() {
  const { classId } = useParams<{ classId: string }>();
  const { data: schoolClass, isLoading: classLoading, isError: classError, error: classErr } = useClass(classId);
  const { data: students, isLoading: studentsLoading } = useClassStudents(classId);

  if (classLoading) return <LoadingState />;
  if (classError) return <ErrorState error={classErr} />;
  if (!schoolClass) return null;

  return (
    <div>
      <PageHeader
        title={schoolClass.name}
        description={schoolClass.academic_year ? `سال تحصیلی ${schoolClass.academic_year}` : undefined}
      />

      <h2 className="mb-3 text-sm font-semibold text-muted-foreground">دانش‌آموزان این کلاس</h2>

      {studentsLoading && <LoadingState />}

      {students && students.length === 0 && (
        <EmptyState
          title="هنوز دانش‌آموزی در این کلاس ثبت نشده"
          description="از صفحه «دانش‌آموزان» می‌توانید دانش‌آموز جدید به این کلاس اضافه کنید."
        />
      )}

      {students && students.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {students.map((student) => (
            <Link key={student.id} to={`/students/${student.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <CardContent className="flex items-center justify-between p-4">
                  <span className="font-medium">{student.full_name}</span>
                  {student.student_code && <Badge variant="outline">{student.student_code}</Badge>}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
