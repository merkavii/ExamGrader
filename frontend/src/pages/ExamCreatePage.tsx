// * ==============================================================================
// *                            ExamCreatePage
// * ==============================================================================
// ? Endpoint ها: POST /exams، POST /exams/{id}/questions
// ! فقط انواع سؤالی که Backend واقعاً Grader دارد قابل انتخاب‌اند
// ! (GRADABLE_QUESTION_TYPES در types/domain.ts) - matching/fill_in_blank عمداً
// ! در این فرم نیستند چون تصحیح‌شان هنوز در Backend پیاده نشده.

import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { questionTypeLabel } from "@/components/common/StatusBadges";
import { useAddQuestion, useCreateExam, useExam } from "@/hooks/useExams";
import type { QuestionType } from "@/types/domain";
import { GRADABLE_QUESTION_TYPES } from "@/types/domain";
import type { QuestionCreateRequest } from "@/types/requests";

export function ExamCreatePage() {
  const navigate = useNavigate();
  const [examId, setExamId] = useState<string | undefined>(undefined);
  const [title, setTitle] = useState("");
  const createExam = useCreateExam();
  const { data: exam } = useExam(examId);

  const handleCreateExam = (e: FormEvent) => {
    e.preventDefault();
    createExam.mutate(
      { title },
      {
        onSuccess: (created) => {
          setExamId(created.id);
          toast.success("آزمون ساخته شد - حالا سؤال‌ها را اضافه کنید");
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در ساخت آزمون"),
      }
    );
  };

  // * مرحله ۱: عنوان آزمون - تا وقتی examId نداریم، فرم سؤال نمایش داده نمی‌شود
  if (!examId) {
    return (
      <div className="mx-auto max-w-md">
        <h1 className="mb-6 text-2xl font-bold">ساخت آزمون جدید</h1>
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleCreateExam} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="exam-title">عنوان آزمون</Label>
                <Input
                  id="exam-title"
                  placeholder="مثلاً آزمون فصل دوم علوم"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <Button type="submit" className="w-full" disabled={createExam.isPending || !title.trim()}>
                {createExam.isPending ? "در حال ساخت..." : "ادامه و افزودن سؤال‌ها"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  // * مرحله ۲: افزودن سؤال‌ها به آزمون ساخته‌شده
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          سؤال‌های آزمون را یکی‌یکی اضافه کنید. در هر لحظه می‌توانید به صفحه آزمون بروید.
        </p>
      </div>

      {exam && exam.questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">سؤال‌های اضافه‌شده ({exam.questions.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {exam.questions.map((q, index) => (
              <div key={q.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                <span>
                  {index + 1}. {q.question_text}
                </span>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{questionTypeLabel(q.question_type)}</Badge>
                  <Badge variant="secondary">{q.max_score} نمره</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <QuestionForm examId={examId} />

      <Button variant="secondary" className="w-full" onClick={() => navigate(`/exams/${examId}`)}>
        پایان و مشاهده آزمون
      </Button>
    </div>
  );
}

// * ----------------------------- فرم افزودن یک سؤال -----------------------------

interface RubricRow {
  description: string;
  points: string;
}

function QuestionForm({ examId }: { examId: string }) {
  const addQuestion = useAddQuestion(examId);

  const [questionText, setQuestionText] = useState("");
  const [questionType, setQuestionType] = useState<QuestionType>("multiple_choice");
  const [maxScore, setMaxScore] = useState("1");
  const [topic, setTopic] = useState("");

  const [options, setOptions] = useState<string[]>(["", ""]);
  const [correctOption, setCorrectOption] = useState("");
  const [correctText, setCorrectText] = useState("");
  const [numericValue, setNumericValue] = useState("");
  const [numericTolerance, setNumericTolerance] = useState("0");
  const [essayReference, setEssayReference] = useState("");
  const [rubricRows, setRubricRows] = useState<RubricRow[]>([{ description: "", points: "" }]);

  const resetForm = () => {
    setQuestionText("");
    setMaxScore("1");
    setTopic("");
    setOptions(["", ""]);
    setCorrectOption("");
    setCorrectText("");
    setNumericValue("");
    setNumericTolerance("0");
    setEssayReference("");
    setRubricRows([{ description: "", points: "" }]);
  };

  const rubricPointsSum = rubricRows.reduce((sum, row) => sum + (Number(row.points) || 0), 0);
  // ! این دقیقاً همان قانونی است که Backend (domain/models/exam.py) اجرا می‌کند:
  // ! جمع امتیاز Rubric باید با max_score برابر باشد - اینجا فقط پیشاپیش به
  // ! معلم نشان می‌دهیم تا خطای ۴۲۲ از سرور غافلگیرکننده نباشد.
  const rubricMismatch = questionType === "essay" && rubricPointsSum !== Number(maxScore);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    let payload: QuestionCreateRequest;
    switch (questionType) {
      case "multiple_choice":
        payload = {
          question_text: questionText,
          question_type: "multiple_choice",
          correct_answer: { selected_option: correctOption },
          options: options.filter((o) => o.trim() !== ""),
          max_score: Number(maxScore),
          topic: topic || undefined,
        };
        break;
      case "true_false":
        payload = {
          question_text: questionText,
          question_type: "true_false",
          correct_answer: { selected_option: correctOption },
          max_score: Number(maxScore),
          topic: topic || undefined,
        };
        break;
      case "numeric":
        payload = {
          question_text: questionText,
          question_type: "numeric",
          correct_answer: { numeric_value: Number(numericValue) },
          numeric_tolerance: Number(numericTolerance),
          max_score: Number(maxScore),
          topic: topic || undefined,
        };
        break;
      case "short_answer":
        payload = {
          question_text: questionText,
          question_type: "short_answer",
          correct_answer: { text: correctText },
          max_score: Number(maxScore),
          topic: topic || undefined,
        };
        break;
      case "essay":
        payload = {
          question_text: questionText,
          question_type: "essay",
          correct_answer: { essay_reference: essayReference },
          rubric: {
            criteria: rubricRows.map((row) => ({
              description: row.description,
              points: Number(row.points),
            })),
          },
          max_score: Number(maxScore),
          topic: topic || undefined,
        };
        break;
      default:
        return;
    }

    addQuestion.mutate(payload, {
      onSuccess: () => {
        toast.success("سؤال اضافه شد");
        resetForm();
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در افزودن سؤال"),
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">افزودن سؤال جدید</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>متن سؤال</Label>
            <Textarea value={questionText} onChange={(e) => setQuestionText(e.target.value)} required />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>نوع سؤال</Label>
              <Select value={questionType} onValueChange={(v) => setQuestionType(v as QuestionType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GRADABLE_QUESTION_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {questionTypeLabel(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>نمره این سؤال</Label>
              <Input
                type="number"
                min="0"
                step="0.5"
                value={maxScore}
                onChange={(e) => setMaxScore(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>موضوع سؤال (اختیاری - برای تحلیل نقاط قوت/ضعف)</Label>
            <Input placeholder="مثلاً فتوسنتز" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>

          <Separator />

          {questionType === "multiple_choice" && (
            <MultipleChoiceFields
              options={options}
              setOptions={setOptions}
              correctOption={correctOption}
              setCorrectOption={setCorrectOption}
            />
          )}

          {questionType === "true_false" && (
            <div className="space-y-2">
              <Label>پاسخ صحیح</Label>
              <Select value={correctOption} onValueChange={setCorrectOption}>
                <SelectTrigger>
                  <SelectValue placeholder="انتخاب کنید" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">درست</SelectItem>
                  <SelectItem value="false">غلط</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {questionType === "numeric" && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>پاسخ صحیح</Label>
                <Input
                  type="number"
                  step="any"
                  value={numericValue}
                  onChange={(e) => setNumericValue(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>خطای مجاز (Tolerance)</Label>
                <Input
                  type="number"
                  step="any"
                  min="0"
                  value={numericTolerance}
                  onChange={(e) => setNumericTolerance(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          {questionType === "short_answer" && (
            <div className="space-y-2">
              <Label>پاسخ صحیح</Label>
              <Input value={correctText} onChange={(e) => setCorrectText(e.target.value)} required />
            </div>
          )}

          {questionType === "essay" && (
            <EssayFields
              essayReference={essayReference}
              setEssayReference={setEssayReference}
              rubricRows={rubricRows}
              setRubricRows={setRubricRows}
              rubricPointsSum={rubricPointsSum}
              maxScore={maxScore}
              mismatch={rubricMismatch}
            />
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={addQuestion.isPending || rubricMismatch || !questionText.trim()}
          >
            <Plus className="h-4 w-4" />
            {addQuestion.isPending ? "در حال افزودن..." : "افزودن این سؤال"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function MultipleChoiceFields({
  options,
  setOptions,
  correctOption,
  setCorrectOption,
}: {
  options: string[];
  setOptions: (options: string[]) => void;
  correctOption: string;
  setCorrectOption: (value: string) => void;
}) {
  return (
    <div className="space-y-3">
      <Label>گزینه‌ها</Label>
      {options.map((option, index) => (
        <div key={index} className="flex items-center gap-2">
          <Input
            placeholder={`گزینه ${index + 1}`}
            value={option}
            onChange={(e) => {
              const next = [...options];
              next[index] = e.target.value;
              setOptions(next);
            }}
          />
          {options.length > 2 && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setOptions(options.filter((_, i) => i !== index))}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          )}
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => setOptions([...options, ""])}>
        <Plus className="h-4 w-4" />
        افزودن گزینه
      </Button>

      <div className="space-y-2 pt-2">
        <Label>گزینه صحیح</Label>
        <Select value={correctOption} onValueChange={setCorrectOption}>
          <SelectTrigger>
            <SelectValue placeholder="انتخاب کنید" />
          </SelectTrigger>
          <SelectContent>
            {options
              .filter((o) => o.trim() !== "")
              .map((option, index) => (
                <SelectItem key={index} value={option}>
                  {option}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

function EssayFields({
  essayReference,
  setEssayReference,
  rubricRows,
  setRubricRows,
  rubricPointsSum,
  maxScore,
  mismatch,
}: {
  essayReference: string;
  setEssayReference: (value: string) => void;
  rubricRows: RubricRow[];
  setRubricRows: (rows: RubricRow[]) => void;
  rubricPointsSum: number;
  maxScore: string;
  mismatch: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>پاسخ مرجع (نمونه)</Label>
        <Textarea value={essayReference} onChange={(e) => setEssayReference(e.target.value)} required />
      </div>

      <div className="space-y-3">
        <Label>معیارهای نمره‌دهی (Rubric)</Label>
        {rubricRows.map((row, index) => (
          <div key={index} className="flex items-center gap-2">
            <Input
              placeholder="توضیح معیار - مثلاً اشاره به نور"
              value={row.description}
              onChange={(e) => {
                const next = [...rubricRows];
                next[index] = { ...next[index], description: e.target.value };
                setRubricRows(next);
              }}
              className="flex-1"
            />
            <Input
              type="number"
              step="0.5"
              min="0"
              placeholder="امتیاز"
              value={row.points}
              onChange={(e) => {
                const next = [...rubricRows];
                next[index] = { ...next[index], points: e.target.value };
                setRubricRows(next);
              }}
              className="w-24"
            />
            {rubricRows.length > 1 && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setRubricRows(rubricRows.filter((_, i) => i !== index))}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            )}
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setRubricRows([...rubricRows, { description: "", points: "" }])}
        >
          <Plus className="h-4 w-4" />
          افزودن معیار
        </Button>

        <p className={mismatch ? "text-sm text-destructive" : "text-sm text-muted-foreground"}>
          جمع امتیاز معیارها: {rubricPointsSum} از {maxScore || 0}
          {mismatch && " - باید دقیقاً با نمره سؤال برابر باشد"}
        </p>
      </div>
    </div>
  );
}
