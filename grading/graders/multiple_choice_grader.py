# * ==============================================================================
# *                        MultipleChoiceGrader
# * ==============================================================================
# ? مقایسه مستقیم گزینه انتخابی دانش‌آموز با گزینه صحیح - بدون نیاز به AI.

from domain.models.exam import Question
from domain.models.student import StudentAnswer
from grading.base_grader import BaseGrader
from grading.rule_based_result import build_deterministic_result


class MultipleChoiceGrader(BaseGrader):
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
        return build_deterministic_result(
            question_id=question.id,
            student_id=student_answer.student_id,
            exam_id=question.exam_id,
            score=question.max_score if is_correct else 0,
            max_score=question.max_score,
            reasoning=(
                f'پاسخ دانش‌آموز "{selected}" با پاسخ صحیح "{correct}" مطابقت دارد.'
                if is_correct
                else f'پاسخ دانش‌آموز "{selected}" بود؛ پاسخ صحیح "{correct}" است.'
            ),
            graded_by=self.__class__.__name__,
        )
