# * ==============================================================================
# *                          ShortAnswerGrader
# * ==============================================================================
# ? برخلاف EssayGrader که Rubric دارد، این کلاس فقط تشخیص می‌دهد پاسخ دانش‌آموز
# ? از نظر معنایی درست است یا نه (بدون نمره جزئی - یا کامل یا صفر).
#
# ! todo اگر در آینده نیاز به Grader قانون‌محور سریع‌تر برای پاسخ کوتاه شد
# ! todo (مثلاً مقایسه دقیق رشته‌ای قبل از رفتن سراغ LLM)، آن منطق باید در یک
# ! todo کلاس جدا (مثلاً ExactMatchShortAnswerGrader) پیاده شود، نه اینجا -
# ! todo تا مسئولیت این کلاس (معنایی/LLM-based) خالص بماند.

from ai.json_response_parser import parse_json_response
from ai.llm_client import LLMClient
from ai.prompts.short_answer_grading_prompt import build_short_answer_grading_prompt
from domain.models.exam import Question
from domain.models.student import StudentAnswer
from grading.base_grader import BaseGrader
from grading.llm_based_result import build_llm_based_result
from grading.rule_based_result import build_deterministic_result


class ShortAnswerGrader(BaseGrader):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def grade(self, question: Question, student_answer: StudentAnswer):
        student_text = student_answer.answer_content.text

        if not student_text:
            return build_deterministic_result(
                question_id=question.id,
                student_id=student_answer.student_id,
                exam_id=question.exam_id,
                score=0,
                max_score=question.max_score,
                reasoning="دانش‌آموز پاسخی برای این سؤال ثبت نکرده است.",
                graded_by=self.__class__.__name__,
            )

        prompt = build_short_answer_grading_prompt(
            question_text=question.question_text,
            reference_answer=question.correct_answer.text,
            student_answer=student_text,
        )

        try:
            raw_response = self._llm_client.complete(prompt)
            parsed = parse_json_response(raw_response)
            is_correct = bool(parsed["is_correct"])
            confidence = float(parsed["confidence"])
            reasoning = parsed["reasoning"]
        except (ValueError, KeyError, TypeError, ConnectionError) as error:
            return build_llm_based_result(
                question_id=question.id,
                student_id=student_answer.student_id,
                exam_id=question.exam_id,
                score=0,
                max_score=question.max_score,
                reasoning=f"خطا در دریافت یا تفسیر پاسخ مدل: {error}",
                grading_confidence=0,
                graded_by=self.__class__.__name__,
            )

        return build_llm_based_result(
            question_id=question.id,
            student_id=student_answer.student_id,
            exam_id=question.exam_id,
            score=question.max_score if is_correct else 0,
            max_score=question.max_score,
            reasoning=reasoning,
            grading_confidence=confidence,
            graded_by=self.__class__.__name__,
        )
