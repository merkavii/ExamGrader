// * ==============================================================================
// *                              DashboardPage
// * ==============================================================================
// ? Endpoint های استفاده‌شده: GET /classes, GET /students, GET /exams,
// ? GET /review-queue, GET /exams/{id}/results (به‌ازای هر آزمون - نگاه کن
// ? به توضیح useDashboardStats.ts)

import { GraduationCap, ListChecks, School, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { useDashboardStats } from "@/hooks/useDashboardStats";

const STAT_CARDS = [
  { key: "classCount" as const, label: "تعداد کلاس‌ها", icon: School, href: "/classes" },
  { key: "studentCount" as const, label: "تعداد دانش‌آموزان", icon: Users, href: "/students" },
  { key: "examCount" as const, label: "تعداد آزمون‌ها", icon: GraduationCap, href: "/exams" },
  {
    key: "needsReviewCount" as const,
    label: "نیازمند بازبینی",
    icon: ListChecks,
    href: "/review-queue",
    highlight: true,
  },
];

export function DashboardPage() {
  const { data: stats, isLoading, isError, error } = useDashboardStats();

  return (
    <div>
      <PageHeader title="داشبورد" description="خلاصه وضعیت فعلی سامانه" />

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {stats && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STAT_CARDS.map((card) => (
              <Link key={card.key} to={card.href}>
                <Card className="transition-shadow hover:shadow-md">
                  <CardContent className="flex items-center justify-between p-5">
                    <div>
                      <p className="text-sm text-muted-foreground">{card.label}</p>
                      <p
                        className={
                          card.highlight && stats[card.key] > 0
                            ? "mt-1 text-3xl font-bold text-warning"
                            : "mt-1 text-3xl font-bold"
                        }
                      >
                        {stats[card.key]}
                      </p>
                    </div>
                    <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <card.icon className="h-5 w-5" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">وضعیت کلی تصحیح</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                تا این لحظه{" "}
                <span className="font-semibold text-foreground">{stats.gradedSheetCount}</span>{" "}
                کارنامه (نتیجه دانش‌آموز-آزمون) تصحیح و ذخیره شده است.
                {stats.needsReviewCount > 0 && (
                  <>
                    {" "}
                    از این میان،{" "}
                    <span className="font-semibold text-warning">{stats.needsReviewCount}</span>{" "}
                    مورد نیازمند بازبینی معلم است.
                  </>
                )}
              </p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
