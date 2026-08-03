# * ==============================================================================
# *                        Tests: ReviewQueue
# * ==============================================================================

import pytest

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult
from confidence.review_queue import InvalidOverrideScoreError, ReviewQueue


def _grade_result(status: GradingStatus, max_score: float = 2) -> GradeResult:
    return GradeResult(
        question_id="q1",
        student_id="s1",
        exam_id="exam-1",
        score=0,
        max_score=max_score,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=50, final_score=50),
        status=status,
        grading_method=GradingMethod.LLM,
        graded_by="EssayGrader",
    )


def test_filter_needing_review_returns_only_flagged_results():
    graded = _grade_result(GradingStatus.GRADED)
    needs_review = _grade_result(GradingStatus.NEEDS_REVIEW)

    filtered = ReviewQueue.filter_needing_review([graded, needs_review])

    assert filtered == [needs_review]


def test_apply_teacher_override_updates_score_reasoning_and_status():
    original = _grade_result(GradingStatus.NEEDS_REVIEW)

    overridden = ReviewQueue.apply_teacher_override(
        original, final_score=1.5, teacher_reasoning="معلم نیمی از نمره را تأیید کرد"
    )

    assert overridden.score == 1.5
    assert overridden.reasoning == "معلم نیمی از نمره را تأیید کرد"
    assert overridden.status == GradingStatus.TEACHER_OVERRIDDEN
    # ! نتیجه اصلی نباید تغییر کند (immutability)
    assert original.status == GradingStatus.NEEDS_REVIEW


def test_apply_teacher_override_sets_grading_method_to_teacher():
    # ? دقیقاً همان نکته‌ای که باید صریح باشد: بعد از Override، منشأ نمره
    # ? دیگر LLM نیست، معلم است - حتی اگر Grader اصلی EssayGrader (LLM) بود.
    original = _grade_result(GradingStatus.NEEDS_REVIEW)
    assert original.grading_method == GradingMethod.LLM

    overridden = ReviewQueue.apply_teacher_override(
        original, final_score=1.5, teacher_reasoning="تأیید معلم"
    )

    assert overridden.grading_method == GradingMethod.TEACHER
    assert overridden.updated_at is not None


def test_apply_teacher_override_rejects_score_above_max():
    original = _grade_result(GradingStatus.NEEDS_REVIEW, max_score=2)
    with pytest.raises(InvalidOverrideScoreError):
        ReviewQueue.apply_teacher_override(original, final_score=3, teacher_reasoning="اشتباه")


def test_apply_teacher_override_rejects_negative_score():
    original = _grade_result(GradingStatus.NEEDS_REVIEW)
    with pytest.raises(InvalidOverrideScoreError):
        ReviewQueue.apply_teacher_override(original, final_score=-1, teacher_reasoning="اشتباه")
