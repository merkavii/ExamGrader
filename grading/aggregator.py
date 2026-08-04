# * ==============================================================================
# *                            ScoreAggregator
# * ==============================================================================
# ? مسئولیت این ماژول: جمع کردن چند GradeResult (یک آزمون، یک دانش‌آموز) به یک
# ? خلاصه نمره واحد. طبق تصمیم معماری قبلی پروژه، نمره نهایی هرگز ذخیره نمی‌شود -
# ? همیشه از روی GradeResult های خام محاسبه می‌شود تا منبع حقیقت تکراری نسازیم.
#
# ! این ماژول فقط جمع می‌زند - هیچ نمره‌ای را تغییر نمی‌دهد و به هیچ
# ! Repository ای وصل نیست (خالص و قابل تست بدون دیتابیس).

from pydantic import BaseModel

from domain.models.enums import GradingStatus
from domain.models.grading_result import GradeResult


class ExamScoreSummary(BaseModel):
    """? خلاصه نمره یک دانش‌آموز برای یک آزمون - خروجی نمایشی، نه Canonical Schema."""

    student_id: str
    exam_id: str
    total_score: float
    max_total_score: float
    percentage: float
    graded_question_count: int
    needs_review_question_count: int


class ScoreAggregator:
    @staticmethod
    def aggregate(
        student_id: str, exam_id: str, grade_results: list[GradeResult]
    ) -> ExamScoreSummary:
        total_score = sum(result.score for result in grade_results)
        max_total_score = sum(result.max_score for result in grade_results)
        needs_review_count = sum(
            1 for result in grade_results if result.status == GradingStatus.NEEDS_REVIEW
        )

        # ! تقسیم بر صفر وقتی آزمون هنوز هیچ سؤالی ندارد یا لیست خالی است.
        percentage = (total_score / max_total_score * 100) if max_total_score > 0 else 0

        return ExamScoreSummary(
            student_id=student_id,
            exam_id=exam_id,
            total_score=total_score,
            max_total_score=max_total_score,
            percentage=round(percentage, 2),
            graded_question_count=len(grade_results),
            needs_review_question_count=needs_review_count,
        )
