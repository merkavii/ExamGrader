# * ==============================================================================
# *                          ClassAnalyticsService
# * ==============================================================================
# ? این ماژول فقط می‌خواند و محاسبه می‌کند - هیچ‌چیز را در دیتابیس تغییر نمی‌دهد.
# ? طبق تصمیم معماری فاز ۵/بررسی معماری قبلی: همه این اعداد از روی GradeResult
# ? های از قبل ذخیره‌شده در لحظه محاسبه می‌شوند، نه یک جدول "آمار" جداگانه.
#
# ! پیش‌نیاز: این سرویس فقط برای آزمونی معنا دارد که قبلاً حداقل یک بار
# ! تصحیح شده (یعنی GradeResult دارد) - اگر نه، participant_count صفر برمی‌گردد،
# ! نه خطا.

from pydantic import BaseModel

from domain.repositories.exam_repository import ExamRepository
from domain.repositories.grade_result_repository import GradeResultRepository
from grading.aggregator import ScoreAggregator


class QuestionAnalytics(BaseModel):
    """? آمار یک سؤال مشخص در میان همه دانش‌آموزانی که به آن پاسخ داده‌اند."""

    question_id: str
    question_text: str
    topic: str | None
    participant_count: int
    correct_percentage: float  # ? درصد دانش‌آموزانی که نمره کامل گرفتند
    average_score_ratio: float  # ? میانگین (نمره/نمره‌کامل) - برای نمره جزئی هم معنادار است


class ExamClassAnalytics(BaseModel):
    """? خلاصه آماری یک آزمون برای کل کلاس."""

    exam_id: str
    participant_count: int
    average_score: float
    average_percentage: float
    highest_score: float
    lowest_score: float
    score_distribution: list[float]  # ? درصد هر دانش‌آموز، برای رسم هیستوگرام در پنل
    question_analytics: list[QuestionAnalytics]  # ? مرتب‌شده: سخت‌ترین سؤال اول
    topic_breakdown: dict[str, float]  # ? topic -> میانگین درصد آن موضوع در این آزمون


class ClassAnalyticsService:
    def __init__(
        self,
        exam_repository: ExamRepository,
        grade_result_repository: GradeResultRepository,
    ) -> None:
        self._exam_repository = exam_repository
        self._grade_result_repository = grade_result_repository

    def analyze_exam(self, exam_id: str) -> ExamClassAnalytics:
        exam = self._exam_repository.get_by_id(exam_id)
        all_results = self._grade_result_repository.get_by_exam(exam_id)

        if not exam or not all_results:
            # ! آزمون بدون نتیجه تصحیح‌شده - آمار خالی معنادار، نه خطا.
            return ExamClassAnalytics(
                exam_id=exam_id,
                participant_count=0,
                average_score=0,
                average_percentage=0,
                highest_score=0,
                lowest_score=0,
                score_distribution=[],
                question_analytics=[],
                topic_breakdown={},
            )

        results_by_student: dict[str, list] = {}
        for result in all_results:
            results_by_student.setdefault(result.student_id, []).append(result)

        student_summaries = [
            ScoreAggregator.aggregate(student_id, exam_id, student_results)
            for student_id, student_results in results_by_student.items()
        ]

        return ExamClassAnalytics(
            exam_id=exam_id,
            participant_count=len(student_summaries),
            average_score=self._mean(s.total_score for s in student_summaries),
            average_percentage=round(
                self._mean(s.percentage for s in student_summaries), 2
            ),
            highest_score=max(s.total_score for s in student_summaries),
            lowest_score=min(s.total_score for s in student_summaries),
            score_distribution=[s.percentage for s in student_summaries],
            question_analytics=self._analyze_questions(exam, all_results),
            topic_breakdown=self._analyze_topics(exam, all_results),
        )

    def _analyze_questions(self, exam, all_results) -> list[QuestionAnalytics]:
        results_by_question: dict[str, list] = {}
        for result in all_results:
            results_by_question.setdefault(result.question_id, []).append(result)

        analytics = []
        for question in exam.questions:
            question_results = results_by_question.get(question.id, [])
            if not question_results:
                continue  # ? سؤالی که هنوز هیچ‌کس برایش تصحیح نشده - در آمار نمی‌آید

            correct_count = sum(
                1 for r in question_results if r.score >= r.max_score
            )
            analytics.append(
                QuestionAnalytics(
                    question_id=question.id,
                    question_text=question.question_text,
                    topic=question.topic,
                    participant_count=len(question_results),
                    correct_percentage=round(
                        correct_count / len(question_results) * 100, 2
                    ),
                    average_score_ratio=round(
                        self._mean(r.score / r.max_score for r in question_results), 4
                    ),
                )
            )

        # ! سخت‌ترین سؤال (کمترین درصد قبولی) اول - این دقیقاً همان چیزی است
        # ! که پنل معلم برای "سؤال‌های سخت" نمایش می‌دهد.
        analytics.sort(key=lambda item: item.correct_percentage)
        return analytics

    def _analyze_topics(self, exam, all_results) -> dict[str, float]:
        topic_by_question_id = {
            question.id: question.topic for question in exam.questions if question.topic
        }

        totals: dict[str, list[float]] = {}
        for result in all_results:
            topic = topic_by_question_id.get(result.question_id)
            if not topic:
                continue  # ? سؤال بدون برچسب موضوعی - در تفکیک موضوعی حساب نمی‌شود
            totals.setdefault(topic, []).append(result.score / result.max_score * 100)

        return {topic: round(self._mean(values), 2) for topic, values in totals.items()}

    @staticmethod
    def _mean(values) -> float:
        values = list(values)
        return sum(values) / len(values) if values else 0
