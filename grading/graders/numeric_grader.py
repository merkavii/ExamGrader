# * ==============================================================================
# *                            NumericGrader
# * ==============================================================================
# ? مقایسه عددی با در نظر گرفتن numeric_tolerance (میزان خطای قابل قبول).
# ? مثال: پاسخ صحیح 9.81 با tolerance=0.05 یعنی هر عددی در بازه [9.76, 9.86] قبول است.

from domain.models.exam import Question
from domain.models.student import StudentAnswer
from grading.base_grader import BaseGrader
from grading.rule_based_result import build_deterministic_result


class NumericGrader(BaseGrader):
    def grade(self, question: Question, student_answer: StudentAnswer):
        student_value = student_answer.answer_content.numeric_value
        correct_value = question.correct_answer.numeric_value
        # ! numeric_tolerance در سطح Question الزامی است (طبق validator در exam.py)
        # ! پس اینجا نیازی به مقدار پیش‌فرض جایگزین نیست.
        tolerance = question.numeric_tolerance

        if student_value is None:
            return build_deterministic_result(
                question_id=question.id,
                student_id=student_answer.student_id,
                exam_id=question.exam_id,
                score=0,
                max_score=question.max_score,
                reasoning="دانش‌آموز پاسخی برای این سؤال ثبت نکرده است.",
                graded_by=self.__class__.__name__,
            )

        difference = abs(student_value - correct_value)
        is_within_tolerance = difference <= tolerance

        return build_deterministic_result(
            question_id=question.id,
            student_id=student_answer.student_id,
            exam_id=question.exam_id,
            score=question.max_score if is_within_tolerance else 0,
            max_score=question.max_score,
            reasoning=(
                f"پاسخ دانش‌آموز ({student_value}) با اختلاف {difference:.4g} از پاسخ "
                f"صحیح ({correct_value})، در محدوده خطای مجاز (±{tolerance}) قرار دارد."
                if is_within_tolerance
                else (
                    f"پاسخ دانش‌آموز ({student_value}) با اختلاف {difference:.4g} از پاسخ "
                    f"صحیح ({correct_value})، خارج از محدوده خطای مجاز (±{tolerance}) است."
                )
            ),
            graded_by=self.__class__.__name__,
        )
