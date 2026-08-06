// * ==============================================================================
// *                          StudentsListPage
// * ==============================================================================
// ? Endpoint ها: GET /students, POST /students, GET /classes (برای نام کلاس و فرم)
// ! جست‌وجو/فیلتر چون Backend endpoint جدا برایش ندارد، سمت Frontend روی همان
// ! لیست کامل دریافت‌شده انجام می‌شود - این تکرار منطق تجاری نیست، فقط فیلتر
// ! نمایشی ساده روی داده‌ای است که از قبل واقعی و کامل دریافت شده.

import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { useClasses } from "@/hooks/useClasses";
import { useCreateStudent, useStudents } from "@/hooks/useStudents";

export function StudentsListPage() {
  const { data: students, isLoading, isError, error } = useStudents();
  const { data: classes } = useClasses();
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const classNameById = useMemo(() => {
    const map = new Map<string, string>();
    classes?.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [classes]);

  const filteredStudents = useMemo(() => {
    if (!students) return [];
    const query = search.trim();
    if (!query) return students;
    return students.filter(
      (s) => s.full_name.includes(query) || s.student_code?.includes(query)
    );
  }, [students, search]);

  return (
    <div>
      <PageHeader
        title="مدیریت دانش‌آموزان"
        description="لیست دانش‌آموزان ثبت‌شده در سامانه"
        actions={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" />
                دانش‌آموز جدید
              </Button>
            </DialogTrigger>
            <CreateStudentDialogContent onDone={() => setDialogOpen(false)} />
          </Dialog>
        }
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {students && students.length > 0 && (
        <div className="relative mb-4 max-w-sm">
          <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="جست‌وجو بر اساس نام یا کد دانش‌آموزی..."
            className="pr-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {students && students.length === 0 && (
        <EmptyState title="هنوز دانش‌آموزی ثبت نشده" description="اولین دانش‌آموز را با دکمه بالا اضافه کنید." />
      )}

      {students && students.length > 0 && filteredStudents.length === 0 && (
        <EmptyState title="نتیجه‌ای یافت نشد" description="عبارت جست‌وجو را تغییر دهید." />
      )}

      {filteredStudents.length > 0 && (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>نام و نام خانوادگی</TableHead>
                <TableHead>کد دانش‌آموزی</TableHead>
                <TableHead>کلاس</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredStudents.map((student) => (
                <TableRow key={student.id} className="cursor-pointer">
                  <TableCell className="p-0">
                    <Link
                      to={`/students/${student.id}`}
                      className="block px-4 py-4 font-medium hover:underline"
                    >
                      {student.full_name}
                    </Link>
                  </TableCell>
                  <TableCell>{student.student_code ?? "—"}</TableCell>
                  <TableCell>
                    {student.class_id ? (
                      <Badge variant="secondary">
                        {classNameById.get(student.class_id) ?? "—"}
                      </Badge>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function CreateStudentDialogContent({ onDone }: { onDone: () => void }) {
  const { data: classes } = useClasses();
  const [fullName, setFullName] = useState("");
  const [studentCode, setStudentCode] = useState("");
  const [classId, setClassId] = useState<string | undefined>(undefined);
  const createStudent = useCreateStudent();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    createStudent.mutate(
      { full_name: fullName, student_code: studentCode || undefined, class_id: classId },
      {
        onSuccess: () => {
          toast.success("دانش‌آموز با موفقیت ثبت شد");
          setFullName("");
          setStudentCode("");
          setClassId(undefined);
          onDone();
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.detail : "خطا در ثبت دانش‌آموز");
        },
      }
    );
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>ثبت دانش‌آموز جدید</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="full-name">نام و نام خانوادگی</Label>
          <Input id="full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="student-code">کد دانش‌آموزی (اختیاری)</Label>
          <Input id="student-code" value={studentCode} onChange={(e) => setStudentCode(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>کلاس (اختیاری)</Label>
          <Select value={classId} onValueChange={setClassId}>
            <SelectTrigger>
              <SelectValue placeholder="بدون کلاس" />
            </SelectTrigger>
            <SelectContent>
              {classes?.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button type="submit" disabled={createStudent.isPending || !fullName.trim()}>
            {createStudent.isPending ? "در حال ثبت..." : "ثبت دانش‌آموز"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
