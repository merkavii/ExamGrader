# * ==============================================================================
# *                              EssayGrader
# * ==============================================================================
# ? تنها مسئولیت این کلاس: گرفتن پاسخ تشریحی متنی، ساخت Prompt بر اساس Rubric،
# ? فراخوانی LLMClient، و تبدیل پاسخ به GradeResult استاندارد.
#
# ! این کلاس نباید بداند پاسخ از عکس آمده یا دستی (source) و نباید مستقیماً
# ! از OllamaProvider استفاده کند - فقط از طریق Interface یعنی LLMClient.

from ai.json_response_parser import parse_json_response
from ai.llm_client import LLMClient
from ai.prompts.essay_grading_prompt import build_essay_grading_prompt
from domain.models.exam import Question
from domain.models.student import StudentAnswer
from grading.base_grader import BaseGrader
from grading.llm_based_result import build_llm_based_result
from grading.rule_based_result import build_deterministic_result


class EssayGrader(BaseGrader):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def grade(self, question: Question, student_answer: StudentAnswer):
        student_text = student_answer.answer_content.text

        if not student_text:
            # ? پاسخ خالی نیازی به LLM ندارد - یک تصمیم قطعی و بدون‌ابهام است.
            return build_deterministic_result(
                question_id=question.id,
                student_id=student_answer.student_id,
                exam_id=question.exam_id,
                score=0,
                max_score=question.max_score,
                reasoning="دانش‌آموز پاسخی برای این سؤال ثبت نکرده است.",
                graded_by=self.__class__.__name__,
            )

        prompt = build_essay_grading_prompt(
            question_text=question.question_text,
            reference_answer=question.correct_answer.essay_reference,
            rubric=question.rubric,
            student_answer=student_text,
        )

        try:
            raw_response = self._llm_client.complete(prompt)
            parsed = parse_json_response(raw_response)
            score = self._sum_criteria_scores(parsed, question.max_score)
            confidence = float(parsed["confidence"])
            reasoning = parsed["reasoning"]
        except (ValueError, KeyError, TypeError, ConnectionError) as error:
            # ! هر خطای غیرمنتظره در ارتباط با مدل یا parse کردن پاسخ، نباید
            # ! کل سیستم را crash کند - باید صراحتاً به بازبینی معلم فرستاده شود.
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
            score=score,
            max_score=question.max_score,
            reasoning=reasoning,
            grading_confidence=confidence,
            graded_by=self.__class__.__name__,
        )

    @staticmethod
    def _sum_criteria_scores(parsed_response: dict, max_score: float) -> float:
        total = sum(
            float(item["points_awarded"]) for item in parsed_response["criteria_scores"]
        )
        # ! دفاعی: حتی اگر مدل اشتباهاً بیشتر از max_score امتیاز داد، اینجا
        # ! محدود می‌شود تا GradeResult validator بعدی خطا ندهد.
        return min(total, max_score)
