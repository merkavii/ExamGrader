# * ==============================================================================
# *              Tests: Exam, GradeResult, ConfidenceScore
# * ==============================================================================

import pytest
from pydantic import ValidationError

from domain.models.enums import GradingMethod, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.grading_result import ConfidenceScore, GradeResult


def _make_true_false_question(exam_id: str) -> Question:
    return Question(
        exam_id=exam_id,
        question_text="زمین گرد است؟",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )


def test_exam_total_score_sums_all_questions():
    exam = Exam(id="exam-1", title="آزمون میان‌ترم")
    question = _make_true_false_question(exam.id)
    exam.questions.append(question)
    assert exam.total_score == 1


def test_exam_rejects_question_with_mismatched_exam_id():
    with pytest.raises(ValidationError):
        Exam(
            id="exam-1",
            title="آزمون میان‌ترم",
            questions=[_make_true_false_question("exam-2")],  # ! exam_id اشتباه
        )


def test_grade_result_rejects_score_above_max():
    with pytest.raises(ValidationError):
        GradeResult(
            question_id="q1",
            student_id="s1",
            exam_id="exam-1",
            score=5,
            max_score=2,
            reasoning="نمره اشتباه به‌عمد برای تست",
            confidence=ConfidenceScore(grading_confidence=90, final_score=90),
            status=GradingStatus.GRADED,
            grading_method=GradingMethod.RULE_BASED,
            graded_by="TrueFalseGrader",
        )


def test_valid_grade_result():
    result = GradeResult(
        question_id="q1",
        student_id="s1",
        exam_id="exam-1",
        score=1,
        max_score=1,
        reasoning="پاسخ دانش‌آموز با پاسخ صحیح یکسان بود",
        confidence=ConfidenceScore(grading_confidence=100, final_score=100),
        status=GradingStatus.GRADED,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )
    assert result.score == result.max_score
