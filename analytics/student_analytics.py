# * ==============================================================================
# *                        StudentAnalyticsService
# * ==============================================================================
# ? مثل ClassAnalyticsService، این هم فقط می‌خواند و محاسبه می‌کند.
# ? همه چیز از GradeResult های ذخیره‌شده در چند آزمون مختلف ساخته می‌شود -
# ? هیچ داده تحلیلی جداگانه‌ای ذخیره نمی‌شود.

from pydantic import BaseModel

from domain.repositories.exam_repository import ExamRepository
from domain.repositories.grade_result_repository import GradeResultRepository
from grading.aggregator import ScoreAggregator


class ExamHistoryEntry(BaseModel):
    """? نمره یک دانش‌آموز در یک آزمون مشخص - یک ردیف از تاریخچه نتایج."""

    exam_id: str
    exam_title: str
    total_score: float
    max_total_score: float
    percentage: float


class StudentAnalytics(BaseModel):
    """? تحلیل کامل یک دانش‌آموز در همه آزمون‌هایی که شرکت کرده."""

    student_id: str
    exam_history: list[ExamHistoryEntry]  # ? مرتب‌شده از قدیم به جدید (created_at آزمون)
    overall_average_percentage: float
    topic_breakdown: dict[str, float]  # ? topic -> میانگین درصد آن دانش‌آموز در آن موضوع

    # ? "improving" / "declining" / "stable" / "insufficient_data"
    # ! این یک برچسب توصیفیِ ساده است (مقایسه اولین با آخرین آزمون با آستانه ۵
    # ! درصد) نه یک مدل پیش‌بینی - برای تحلیل دقیق‌تر روند، پنل معلم باید مستقیماً
    # ! از exam_history (که کامل و مرتب است) نمودار بکشد.
    trend: str


class ClassComparison(BaseModel):
    """? مقایسه نمره یک دانش‌آموز با میانگین کلاس، برای یک آزمون مشخص."""

    exam_id: str
    student_percentage: float
    class_average_percentage: float
    difference: float  # ? مثبت یعنی بالاتر از میانگین کلاس


_TREND_THRESHOLD_PERCENTAGE_POINTS = 5


class StudentAnalyticsService:
    def __init__(
        self,
        exam_repository: ExamRepository,
        grade_result_repository: GradeResultRepository,
    ) -> None:
        self._exam_repository = exam_repository
        self._grade_result_repository = grade_result_repository

    def analyze_student(self, student_id: str) -> StudentAnalytics:
        all_results = self._grade_result_repository.get_by_student(student_id)

        if not all_results:
            return StudentAnalytics(
                student_id=student_id,
                exam_history=[],
                overall_average_percentage=0,
                topic_breakdown={},
                trend="insufficient_data",
            )

        results_by_exam: dict[str, list] = {}
        for result in all_results:
            results_by_exam.setdefault(result.exam_id, []).append(result)

        history_with_dates = []
        for exam_id, exam_results in results_by_exam.items():
            exam = self._exam_repository.get_by_id(exam_id)
            if not exam:
                continue  # ! داده ناسازگار - نباید رخ دهد، ولی صامت رد نمی‌شود
            summary = ScoreAggregator.aggregate(student_id, exam_id, exam_results)
            history_with_dates.append(
                (
                    exam.created_at,
                    ExamHistoryEntry(
                        exam_id=exam_id,
                        exam_title=exam.title,
                        total_score=summary.total_score,
                        max_total_score=summary.max_total_score,
                        percentage=summary.percentage,
                    ),
                )
            )

        history_with_dates.sort(key=lambda item: item[0])
        exam_history = [entry for _, entry in history_with_dates]

        total_score_all = sum(entry.total_score for entry in exam_history)
        max_total_score_all = sum(entry.max_total_score for entry in exam_history)
        overall_average_percentage = round(
            (total_score_all / max_total_score_all * 100) if max_total_score_all > 0 else 0,
            2,
        )

        return StudentAnalytics(
            student_id=student_id,
            exam_history=exam_history,
            overall_average_percentage=overall_average_percentage,
            topic_breakdown=self._analyze_topics(all_results),
            trend=self._determine_trend(exam_history),
        )

    def compare_to_class(
        self, student_id: str, exam_id: str, class_average_percentage: float
    ) -> ClassComparison:
        """
        ? مقایسه با میانگین کلاس. class_average_percentage از
        ? ClassAnalyticsService.analyze_exam(exam_id).average_percentage می‌آید -
        ! این سرویس عمداً خودش ClassAnalyticsService را صدا نمی‌زند تا وابستگی
        ! مستقیم بین دو سرویس تحلیلی ایجاد نشود؛ لایه صداکننده (مثلاً روتر API)
        ! هر دو را جدا فراخوانی و نتیجه را ترکیب می‌کند.
        """
        student_results = self._grade_result_repository.get_by_student_and_exam(
            student_id, exam_id
        )
        summary = ScoreAggregator.aggregate(student_id, exam_id, student_results)

        return ClassComparison(
            exam_id=exam_id,
            student_percentage=summary.percentage,
            class_average_percentage=class_average_percentage,
            difference=round(summary.percentage - class_average_percentage, 2),
        )

    def _analyze_topics(self, all_results) -> dict[str, float]:
        totals: dict[str, list[float]] = {}
        for result in all_results:
            question = self._exam_repository.get_question(result.question_id)
            if not question or not question.topic:
                continue
            totals.setdefault(question.topic, []).append(
                result.score / result.max_score * 100
            )

        return {
            topic: round(sum(values) / len(values), 2) for topic, values in totals.items()
        }

    @staticmethod
    def _determine_trend(exam_history: list[ExamHistoryEntry]) -> str:
        if len(exam_history) < 2:
            return "insufficient_data"

        difference = exam_history[-1].percentage - exam_history[0].percentage
        if difference > _TREND_THRESHOLD_PERCENTAGE_POINTS:
            return "improving"
        if difference < -_TREND_THRESHOLD_PERCENTAGE_POINTS:
            return "declining"
        return "stable"
