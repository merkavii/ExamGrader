# * ==============================================================================
# *          Tests: MultipleChoiceGrader / TrueFalseGrader
# * ==============================================================================

from domain.models.enums import AnswerSource, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.student import AnswerContent, StudentAnswer
from grading.graders.multiple_choice_grader import MultipleChoiceGrader
from grading.graders.true_false_grader import TrueFalseGrader


def _mc_question() -> Question:
    return Question(
        id="q1",
        exam_id="exam-1",
        question_text="کدام گزینه سیاره است؟",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer=CorrectAnswer(selected_option="زمین"),
        options=["ماه", "زمین", "خورشید", "ستاره"],
        max_score=2,
    )


def _answer(question_id: str, selected_option: str | None) -> StudentAnswer:
    return StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id=question_id,
        answer_content=AnswerContent(selected_option=selected_option),
        source=AnswerSource.MANUAL,
    )


def test_multiple_choice_correct_answer_gets_full_score():
    question = _mc_question()
    result = MultipleChoiceGrader().grade(question, _answer("q1", "زمین"))
    assert result.score == 2
    assert result.max_score == 2


def test_multiple_choice_wrong_answer_gets_zero():
    question = _mc_question()
    result = MultipleChoiceGrader().grade(question, _answer("q1", "ماه"))
    assert result.score == 0


def test_multiple_choice_empty_answer_gets_zero_with_clear_reasoning():
    question = _mc_question()
    result = MultipleChoiceGrader().grade(question, _answer("q1", None))
    assert result.score == 0
    assert "ثبت نکرده" in result.reasoning


def test_true_false_correct_answer_gets_full_score():
    question = Question(
        id="q2",
        exam_id="exam-1",
        question_text="آب در صفر درجه یخ می‌زند؟",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    result = TrueFalseGrader().grade(question, _answer("q2", "true"))
    assert result.score == 1


def test_true_false_wrong_answer_gets_zero():
    question = Question(
        id="q2",
        exam_id="exam-1",
        question_text="آب در صفر درجه یخ می‌زند؟",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    result = TrueFalseGrader().grade(question, _answer("q2", "false"))
    assert result.score == 0
