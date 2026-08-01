# * ==============================================================================
# *                          TrueFalseGrader
# * ==============================================================================
# ? از نظر ساختار داده دقیقاً مثل MultipleChoiceGrader است (هر دو selected_option
# ? دارند)، اما عمداً یک کلاس جدا نگه داشته شده چون از نظر دامنه (Domain) دو نوع
# ? سؤال مفهوماً متفاوت‌اند و ممکن است در آینده رفتارشان از هم جدا شود
# ? (مثلاً نمایش متفاوت در پنل معلم، یا امتیاز منفی برای حدس اشتباه در True/False).

from domain.models.exam import Question
from domain.models.student import StudentAnswer
from grading.base_grader import BaseGrader
from grading.rule_based_result import build_deterministic_result


class TrueFalseGrader(BaseGrader):
    def grade(self, question: Question, student_answer: StudentAnswer):
        selected = student_answer.answer_content.selected_option
        correct = question.correct_answer.selected_option

        if selected is None:
            return build_deterministic_result(
                question_id=question.id,
                student_id=student_answer.student_id,
                exam_id=question.exam_id,
                score=0,
                max_score=question.max_score,
                reasoning="دانش‌آموز پاسخی برای این سؤال ثبت نکرده است.",
                graded_by=self.__class__.__name__,
            )

        is_correct = selected == correct
        persian_label = {"true": "درست", "false": "غلط"}
        return build_deterministic_result(
            question_id=question.id,
            student_id=student_answer.student_id,
            exam_id=question.exam_id,
            score=question.max_score if is_correct else 0,
            max_score=question.max_score,
            reasoning=(
                f"پاسخ دانش‌آموز ({persian_label.get(selected, selected)}) صحیح است."
                if is_correct
                else (
                    f"پاسخ دانش‌آموز ({persian_label.get(selected, selected)}) بود؛ "
                    f"پاسخ صحیح ({persian_label.get(correct, correct)}) است."
                )
            ),
            graded_by=self.__class__.__name__,
        )
