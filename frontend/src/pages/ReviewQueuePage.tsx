// * ==============================================================================
// *                            ReviewQueuePage
// * ==============================================================================
// ? Endpoint ها: GET /review-queue (با فیلتر اختیاری exam_id)،
// ? POST /review-queue/{id}/override ، GET /exams (برای فیلتر)

import { useState } from "react";
import type { FormEvent } from "react";
import { toast } from "sonner";
import { ApiError } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { Textarea } from "@/components/ui/textarea";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/StateViews";
import { PageHeader } from "@/components/common/PageHeader";
import { GradingMethodBadge } from "@/components/common/StatusBadges";
import { useExams } from "@/hooks/useExams";
import { useOverrideGradeResult, useReviewQueue } from "@/hooks/useReview";
import type { ReviewQueueItem } from "@/types/domain";

export function ReviewQueuePage() {
  const [examFilter, setExamFilter] = useState<string | undefined>(undefined);
  const { data: exams } = useExams();
  const { data: items, isLoading, isError, error } = useReviewQueue(examFilter);

  return (
    <div>
      <PageHeader
        title="صف بازبینی"
        description="مواردی که سیستم به آن‌ها اطمینان کافی نداشته و نیاز به تأیید یا اصلاح معلم دارند"
      />

      <div className="mb-4 max-w-xs">
        <Select value={examFilter} onValueChange={setExamFilter}>
          <SelectTrigger>
            <SelectValue placeholder="همه آزمون‌ها" />
          </SelectTrigger>
          <SelectContent>
            {exams?.map((exam) => (
              <SelectItem key={exam.id} value={exam.id}>
                {exam.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState error={error} />}

      {items && items.length === 0 && (
        <EmptyState title="صف بازبینی خالی است" description="هیچ موردی نیازمند بررسی معلم نیست." />
      )}

      {items && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <ReviewItemCard key={item.grade_result.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewItemCard({ item }: { item: ReviewQueueItem }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { grade_result: result } = item;

  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="font-medium">{item.question_text}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {item.student_full_name}
              {item.student_code && ` (${item.student_code})`} · {item.exam_title}
              {item.question_topic && ` · ${item.question_topic}`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <GradingMethodBadge method={result.grading_method} />
            <Badge variant="warning">اطمینان {result.confidence.final_score}٪</Badge>
          </div>
        </div>

        <p className="text-sm">{result.reasoning}</p>

        <div className="flex items-center justify-between border-t pt-3">
          <span className="text-sm text-muted-foreground">
            نمره پیشنهادی: <span className="font-semibold text-foreground">{result.score}</span> از{" "}
            {result.max_score}
          </span>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">بررسی و ثبت نظر</Button>
            </DialogTrigger>
            <OverrideDialogContent
              item={item}
              onDone={() => setDialogOpen(false)}
            />
          </Dialog>
        </div>
      </CardContent>
    </Card>
  );
}

function OverrideDialogContent({ item, onDone }: { item: ReviewQueueItem; onDone: () => void }) {
  const { grade_result: result } = item;
  const [score, setScore] = useState(String(result.score));
  const [reasoning, setReasoning] = useState(result.reasoning);
  const override = useOverrideGradeResult();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    override.mutate(
      { gradeResultId: result.id, payload: { final_score: Number(score), teacher_reasoning: reasoning } },
      {
        onSuccess: () => {
          toast.success("نظر معلم ثبت شد");
          onDone();
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.detail : "خطا در ثبت نظر"),
      }
    );
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>بررسی نتیجه تصحیح</DialogTitle>
      </DialogHeader>

      <div className="space-y-2 rounded-md bg-muted p-3 text-sm text-muted-foreground">
        <p>دلیل تصحیح فعلی سیستم: {result.reasoning}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="override-score">نمره نهایی (حداکثر {result.max_score})</Label>
          <Input
            id="override-score"
            type="number"
            min={0}
            max={result.max_score}
            step="0.5"
            value={score}
            onChange={(e) => setScore(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="override-reasoning">دلیل تصمیم معلم</Label>
          <Textarea
            id="override-reasoning"
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            required
          />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={override.isPending}>
            {override.isPending ? "در حال ثبت..." : "ثبت نظر نهایی"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
