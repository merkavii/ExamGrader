# * ==============================================================================
# *                       Tests: NumericGrader
# * ==============================================================================

from domain.models.enums import AnswerSource, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.student import AnswerContent, StudentAnswer
from grading.graders.numeric_grader import NumericGrader


def _numeric_question() -> Question:
    return Question(
        id="q1",
        exam_id="exam-1",
        question_text="شتاب جاذبه زمین؟",
        question_type=QuestionType.NUMERIC,
        correct_answer=CorrectAnswer(numeric_value=9.81),
        numeric_tolerance=0.05,
        max_score=1,
    )


def _answer(numeric_value: float | None) -> StudentAnswer:
    return StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id="q1",
        answer_content=AnswerContent(numeric_value=numeric_value),
        source=AnswerSource.MANUAL,
    )


def test_exact_match_gets_full_score():
    result = NumericGrader().grade(_numeric_question(), _answer(9.81))
    assert result.score == 1


def test_within_tolerance_gets_full_score():
    # ? 9.8 در بازه [9.76, 9.86] است -> قبول
    result = NumericGrader().grade(_numeric_question(), _answer(9.8))
    assert result.score == 1


def test_exactly_at_tolerance_boundary_gets_full_score():
    # ! مرز دقیق tolerance - نباید به‌خاطر خطای اعشاری رد شود
    result = NumericGrader().grade(_numeric_question(), _answer(9.86))
    assert result.score == 1


def test_outside_tolerance_gets_zero():
    result = NumericGrader().grade(_numeric_question(), _answer(9.9))
    assert result.score == 0


def test_missing_answer_gets_zero():
    result = NumericGrader().grade(_numeric_question(), _answer(None))
    assert result.score == 0
    assert "ثبت نکرده" in result.reasoning
