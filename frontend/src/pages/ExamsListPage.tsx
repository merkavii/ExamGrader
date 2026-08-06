// * ==============================================================================
// *                            ExamsListPage
// * ==============================================================================
// ? Endpoint: GET /exams

import { Link } from "react-router-dom";
import { FileText, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { useExams } from "@/hooks/useExams";

export function ExamsListPage() {
  const { data: exams, isLoading, isError, error } = useExams();

  return (
    <div>
      <PageHeader
        title="مدیریت آزمون‌ها"
        description="آزمون‌های ساخته‌شده در سامانه"
        actions={
          <Button asChild>
            <Link to="/exams/new">
              <Plus className="h-4 w-4" />
              آزمون جدید
            </Link>
          </Button>
        }
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {exams && exams.length === 0 && (
        <EmptyState title="هنوز آزمونی ساخته نشده" description="اولین آزمون را با دکمه بالا بسازید." />
      )}

      {exams && exams.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {exams.map((exam) => (
            <Link key={exam.id} to={`/exams/${exam.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardContent className="flex items-start justify-between p-5">
                  <div>
                    <p className="font-semibold">{exam.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {new Date(exam.created_at).toLocaleDateString("fa-IR")}
                    </p>
                  </div>
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {exam.questions.length} سؤال
                  </Badge>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
