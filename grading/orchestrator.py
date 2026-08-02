# * ==============================================================================
# *                          GradingOrchestrator
# * ==============================================================================
# ? این کلاس بر اساس question_type، Grader مناسب را از یک Registry انتخاب
# ? و صدا می‌زند. این پیاده‌سازی Strategy Pattern است.
#
# ! این کلاس نباید منطق نمره‌دهی هیچ نوع سؤالی را مستقیماً پیاده‌سازی کند -
# ! فقط مسئول "انتخاب" است، نه "تصحیح".

from domain.models.enums import QuestionType
from domain.models.exam import Question
from domain.models.grading_result import GradeResult
from domain.models.student import StudentAnswer
from ai.llm_client import LLMClient
from grading.base_grader import BaseGrader
from grading.graders.essay_grader import EssayGrader
from grading.graders.multiple_choice_grader import MultipleChoiceGrader
from grading.graders.numeric_grader import NumericGrader
from grading.graders.short_answer_grader import ShortAnswerGrader
from grading.graders.true_false_grader import TrueFalseGrader


class UnsupportedQuestionTypeError(Exception):
    """? برای انواع سؤالی که هنوز Grader ندارند (مثلاً Matching در فاز ۳)."""


class GradingOrchestrator:
    def __init__(
        self,
        graders: dict[QuestionType, BaseGrader] | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        # ? اگر graders صریحاً داده شود (مثلاً در تست‌ها)، همان استفاده می‌شود
        # ? و llm_client نادیده گرفته می‌شود - کنترل کامل دست صداکننده است.
        if graders is not None:
            self._graders: dict[QuestionType, BaseGrader] = graders
            return

        self._graders = {
            QuestionType.MULTIPLE_CHOICE: MultipleChoiceGrader(),
            QuestionType.TRUE_FALSE: TrueFalseGrader(),
            QuestionType.NUMERIC: NumericGrader(),
        }

        # ! ShortAnswerGrader و EssayGrader فقط وقتی ثبت می‌شوند که llm_client
        # ! داده شده باشد - چون بدون آن، ساخت این دو Grader اصلاً معنا ندارد.
        # ! این یعنی رفتار فاز ۲ (بدون llm_client -> UnsupportedQuestionTypeError
        # ! برای SHORT_ANSWER/ESSAY) دست‌نخورده می‌ماند.
        if llm_client is not None:
            self._graders[QuestionType.SHORT_ANSWER] = ShortAnswerGrader(llm_client)
            self._graders[QuestionType.ESSAY] = EssayGrader(llm_client)

    def grade_question(
        self, question: Question, student_answer: StudentAnswer
    ) -> GradeResult:
        grader = self._graders.get(question.question_type)
        if grader is None:
            raise UnsupportedQuestionTypeError(
                f"No grader registered for question_type={question.question_type}"
            )

        # ! اطمینان از این‌که پاسخ واقعاً متعلق به همین سؤال است - جلوگیری از
        # ! باگ ظریف که یک StudentAnswer اشتباه به Grader سؤال دیگری داده شود.
        if student_answer.question_id != question.id:
            raise ValueError(
                f"StudentAnswer.question_id ({student_answer.question_id}) does not "
                f"match Question.id ({question.id})"
            )

        return grader.grade(question, student_answer)
