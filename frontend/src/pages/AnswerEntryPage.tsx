// * ==============================================================================
// *                            AnswerEntryPage
// * ==============================================================================
// ? Endpoint ها: GET /exams/{id} (سؤال‌ها)، GET /exams/{id}/students/{id}/answers
// ? (پیش‌پرشدن با پاسخ قبلی در صورت وجود)، POST .../answers (ثبت)
//
// ! پاسخ خالی یک حالت معتبر است: هیچ فیلدی required نیست و ارسال با مقدار خالی
// ! خطای Validation نمایش نمی‌دهد - دقیقاً طبق قانون صریح این صفحه.

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { useExam } from "@/hooks/useExams";
import { useStudent } from "@/hooks/useStudents";
import { useStudentAnswers, useSubmitAnswers } from "@/hooks/useSheets";
import type { AnswerContent } from "@/types/domain";

export function AnswerEntryPage() {
  const { examId, studentId } = useParams<{ examId: string; studentId: string }>();
  const { data: exam, isLoading: examLoading, isError, error } = useExam(examId);
  const { data: student } = useStudent(studentId);
  const { data: existingAnswers } = useStudentAnswers(examId, studentId);
  const submitAnswers = useSubmitAnswers(examId!, studentId!);
  const navigate = useNavigate();

  const [answersByQuestion, setAnswersByQuestion] = useState<Record<string, AnswerContent>>({});

  // ? پیش‌پرکردن فرم با پاسخ‌های قبلاً ثبت‌شده - فقط یک‌بار وقتی داده رسید
  useEffect(() => {
    if (!existingAnswers) return;
    const initial: Record<string, AnswerContent> = {};
    for (const answer of existingAnswers) {
      initial[answer.question_id] = answer.answer_content;
    }
    setAnswersByQuestion((prev) => ({ ...initial, ...prev }));
  }, [existingAnswers]);

  if (examLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!exam || !examId || !studentId) return null;

  const updateAnswer = (questionId: string, content: AnswerContent) => {
    setAnswersByQuestion((prev) => ({ ...prev, [questionId]: content }));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    submitAnswers.mutate(
      {
        answers: exam.questions.map((q) => ({
          question_id: q.id,
          // ? اگر معلم چیزی برای این سؤال وارد نکرده، یک AnswerContent کاملاً
          // ? خالی ارسال می‌شود - Backend این را وضعیت معتبر "بدون پاسخ" می‌داند.
          answer_content: answersByQuestion[q.id] ?? {},
        })),
      },
      {
        onSuccess: () => {
          toast.success("پاسخ‌ها ثبت شد");
          navigate(`/exams/${examId}`);
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در ثبت پاسخ‌ها"),
      }
    );
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title={`ثبت پاسخ - ${student?.full_name ?? "..."}`}
        description={exam.title}
      />

      <form onSubmit={handleSubmit} className="space-y-4">
        {exam.questions.map((question, index) => (
          <Card key={question.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {index + 1}. {question.question_text}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <QuestionAnswerInput
                question={question}
                value={answersByQuestion[question.id] ?? {}}
                onChange={(content) => updateAnswer(question.id, content)}
              />
            </CardContent>
          </Card>
        ))}

        <Button type="submit" className="w-full" disabled={submitAnswers.isPending}>
          {submitAnswers.isPending ? "در حال ثبت..." : "ثبت پاسخ‌ها"}
        </Button>
      </form>
    </div>
  );
}

function QuestionAnswerInput({
  question,
  value,
  onChange,
}: {
  question: import("@/types/domain").Question;
  value: AnswerContent;
  onChange: (content: AnswerContent) => void;
}) {
  switch (question.question_type) {
    case "multiple_choice":
      return (
        <Select
          value={value.selected_option ?? undefined}
          onValueChange={(v) => onChange({ selected_option: v })}
        >
          <SelectTrigger>
            {/* ? بدون پاسخ = معتبر - جای‌نگهدار فقط نمایشی است، هیچ اجباری وجود ندارد */}
            <SelectValue placeholder="بدون پاسخ" />
          </SelectTrigger>
          <SelectContent>
            {question.options?.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );

    case "true_false":
      return (
        <Select
          value={value.selected_option ?? undefined}
          onValueChange={(v) => onChange({ selected_option: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="بدون پاسخ" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="true">درست</SelectItem>
            <SelectItem value="false">غلط</SelectItem>
          </SelectContent>
        </Select>
      );

    case "numeric":
      return (
        <div className="max-w-xs space-y-1">
          <Input
            type="number"
            step="any"
            placeholder="بدون پاسخ"
            value={value.numeric_value ?? ""}
            onChange={(e) =>
              onChange({
                numeric_value: e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
          <Label className="text-xs font-normal text-muted-foreground">
            نمره کامل: {question.correct_answer.numeric_value} (خطای مجاز: ±{question.numeric_tolerance})
          </Label>
        </div>
      );

    case "short_answer":
      return (
        <Input
          placeholder="بدون پاسخ"
          value={value.text ?? ""}
          onChange={(e) => onChange({ text: e.target.value })}
        />
      );

    case "essay":
      return (
        <Textarea
          placeholder="بدون پاسخ"
          rows={4}
          value={value.text ?? ""}
          onChange={(e) => onChange({ text: e.target.value })}
        />
      );

    default:
      return <p className="text-sm text-muted-foreground">این نوع سؤال هنوز در فرم پشتیبانی نمی‌شود.</p>;
  }
}
