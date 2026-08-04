# * ==============================================================================
# *                            GradingService
# * ==============================================================================
# ? این کلاس همان جایی است که در فاز ۴ به آن اشاره شد: اتصال واقعی سه بلوک آماده
# ? به هم -
# ?   GradingOrchestrator (فاز ۲/۳) -> تولید GradeResult خام
# ?   ConfidenceEngine (فاز ۴)      -> تکمیل confidence و تعیین status نهایی
# ?   GradeResultRepository (فاز ۵) -> ذخیره نتیجه نهایی
# ?
# ! این کلاس در app/routers نیست چون منطق تجاری است، نه HTTP - باید بدون
# ! FastAPI هم قابل تست و استفاده باشد (مثلاً از یک اسکریپت CLI در آینده).

from domain.models.enums import AnswerSource
from domain.models.exam import Question
from domain.models.grading_result import GradeResult
from domain.models.student import AnswerContent, StudentAnswer
from domain.repositories.exam_repository import ExamRepository
from domain.repositories.grade_result_repository import GradeResultRepository
from domain.repositories.student_repository import (
    StudentAnswerRepository,
    StudentRepository,
)
from confidence.confidence_engine import ConfidenceEngine
from grading.aggregator import ExamScoreSummary, ScoreAggregator
from grading.orchestrator import GradingOrchestrator


class ExamNotFoundError(Exception):
    pass


class StudentNotFoundError(Exception):
    pass


def _build_empty_answer(exam_id: str, student_id: str, question: Question) -> StudentAnswer:
    # ? وقتی دانش‌آموز اصلاً پاسخی برای یک سؤال ثبت نکرده، به‌جای رد کردن آن
    # ? سؤال، یک StudentAnswer خالی (غیر ذخیره‌شده) به Grader می‌دهیم - همه
    # ? Grader ها از قبل برای answer_content خالی، نمره صفر و دلیل واضح تولید
    # ? می‌کنند (نگاه کن به build_deterministic_result/build_llm_based_result).
    return StudentAnswer(
        exam_id=exam_id,
        student_id=student_id,
        question_id=question.id,
        answer_content=AnswerContent(),
        source=AnswerSource.MANUAL,
    )


class GradingService:
    def __init__(
        self,
        exam_repository: ExamRepository,
        student_repository: StudentRepository,
        student_answer_repository: StudentAnswerRepository,
        grade_result_repository: GradeResultRepository,
        orchestrator: GradingOrchestrator,
        confidence_engine: ConfidenceEngine | None = None,
    ) -> None:
        self._exam_repository = exam_repository
        self._student_repository = student_repository
        self._student_answer_repository = student_answer_repository
        self._grade_result_repository = grade_result_repository
        self._orchestrator = orchestrator
        self._confidence_engine = confidence_engine or ConfidenceEngine()

    def grade_student(self, exam_id: str, student_id: str) -> list[GradeResult]:
        """
        ? یک برگه (یک دانش‌آموز، یک آزمون) را تصحیح، ذخیره و برمی‌گرداند.

        ! Idempotent است: اگر قبلاً تصحیح شده بود، نتایج جدید جایگزین قبلی
        ! می‌شوند (طبق UNIQUE constraint در GradeResultORM) - این همان قابلیت
        ! "تصحیح مجدد یک برگه" است که از ابتدای پروژه خواسته شده بود.
        """
        exam = self._exam_repository.get_by_id(exam_id)
        if not exam:
            raise ExamNotFoundError(f"Exam {exam_id} not found")
        if not self._student_repository.get_by_id(student_id):
            raise StudentNotFoundError(f"Student {student_id} not found")

        existing_answers = {
            answer.question_id: answer
            for answer in self._student_answer_repository.get_by_student_and_exam(
                student_id, exam_id
            )
        }

        results: list[GradeResult] = []
        for question in exam.questions:
            student_answer = existing_answers.get(
                question.id
            ) or _build_empty_answer(exam_id, student_id, question)

            raw_result = self._orchestrator.grade_question(question, student_answer)
            # ? در این فاز هنوز image_quality/extraction_confidence نداریم
            # ? (Extraction Layer بعد از MVP می‌آید) - ConfidenceEngine با همان
            # ? یک منبع (grading_confidence) هم درست کار می‌کند.
            final_result = self._confidence_engine.evaluate(raw_result)

            self._grade_result_repository.save(final_result)
            results.append(final_result)

        return results

    def grade_exam(self, exam_id: str) -> dict[str, list[GradeResult]]:
        """? تصحیح دسته‌ای همه دانش‌آموزانی که برای این آزمون پاسخ ثبت کرده‌اند."""
        if not self._exam_repository.get_by_id(exam_id):
            raise ExamNotFoundError(f"Exam {exam_id} not found")

        students = self._student_repository.list_by_exam(exam_id)
        return {
            student.id: self.grade_student(exam_id, student.id) for student in students
        }

    def get_exam_results(self, exam_id: str) -> list[ExamScoreSummary]:
        """
        ? خلاصه نمره همه دانش‌آموزان یک آزمون - از روی GradeResult های از قبل
        ? ذخیره‌شده، بدون تصحیح مجدد. برای نمایش تب Results در پنل معلم.
        """
        if not self._exam_repository.get_by_id(exam_id):
            raise ExamNotFoundError(f"Exam {exam_id} not found")

        all_results = self._grade_result_repository.get_by_exam(exam_id)

        results_by_student: dict[str, list[GradeResult]] = {}
        for result in all_results:
            results_by_student.setdefault(result.student_id, []).append(result)

        return [
            ScoreAggregator.aggregate(student_id, exam_id, student_results)
            for student_id, student_results in results_by_student.items()
        ]
