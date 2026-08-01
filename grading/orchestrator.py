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
from grading.base_grader import BaseGrader
from grading.graders.multiple_choice_grader import MultipleChoiceGrader
from grading.graders.numeric_grader import NumericGrader
from grading.graders.true_false_grader import TrueFalseGrader


class UnsupportedQuestionTypeError(Exception):
    """? برای انواع سؤالی که هنوز Grader ندارند (مثلاً Essay در فاز ۲)."""


class GradingOrchestrator:
    def __init__(self, graders: dict[QuestionType, BaseGrader] | None = None) -> None:
        # ? Registry پیش‌فرض فقط شامل Grader های قانون‌محور فاز ۲ است.
        # ? در فاز ۳، Essay/ShortAnswer اضافه می‌شوند - فقط با یک خط جدید اینجا،
        # ? بدون تغییر در بقیه این کلاس (Open/Closed Principle).
        self._graders: dict[QuestionType, BaseGrader] = graders or {
            QuestionType.MULTIPLE_CHOICE: MultipleChoiceGrader(),
            QuestionType.TRUE_FALSE: TrueFalseGrader(),
            QuestionType.NUMERIC: NumericGrader(),
        }

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
