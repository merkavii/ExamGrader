// * ==============================================================================
// *                            ClassesListPage
// * ==============================================================================
// ? Endpoint ها: GET /classes, POST /classes

import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { useClasses, useCreateClass } from "@/hooks/useClasses";
import { toast } from "sonner";
import { ApiError } from "@/api/client";

export function ClassesListPage() {
  const { data: classes, isLoading, isError, error } = useClasses();
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div>
      <PageHeader
        title="مدیریت کلاس‌ها"
        description="کلاس‌ها یا گروه‌های آموزشی خود را مدیریت کنید"
        actions={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" />
                کلاس جدید
              </Button>
            </DialogTrigger>
            <CreateClassDialogContent onDone={() => setDialogOpen(false)} />
          </Dialog>
        }
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {classes && classes.length === 0 && (
        <EmptyState title="هنوز کلاسی ثبت نشده" description="اولین کلاس را با دکمه «کلاس جدید» بسازید." />
      )}

      {classes && classes.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {classes.map((schoolClass) => (
            <Link key={schoolClass.id} to={`/classes/${schoolClass.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardContent className="p-5">
                  <p className="font-semibold">{schoolClass.name}</p>
                  {schoolClass.academic_year && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      سال تحصیلی {schoolClass.academic_year}
                    </p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateClassDialogContent({ onDone }: { onDone: () => void }) {
  const [name, setName] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const createClass = useCreateClass();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    createClass.mutate(
      { name, academic_year: academicYear || undefined },
      {
        onSuccess: () => {
          toast.success("کلاس با موفقیت ساخته شد");
          setName("");
          setAcademicYear("");
          onDone();
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.detail : "خطا در ساخت کلاس");
        },
      }
    );
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>ساخت کلاس جدید</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="class-name">نام کلاس</Label>
          <Input
            id="class-name"
            placeholder="مثلاً هفتم الف"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="academic-year">سال تحصیلی (اختیاری)</Label>
          <Input
            id="academic-year"
            placeholder="مثلاً ۱۴۰۴-۱۴۰۵"
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={createClass.isPending || !name.trim()}>
            {createClass.isPending ? "در حال ساخت..." : "ساخت کلاس"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
