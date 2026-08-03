# * ==============================================================================
# *                      Tests: ConfidenceEngine
# * ==============================================================================

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult
from confidence.confidence_engine import ConfidenceEngine, confidence_tier


def _grade_result(grading_confidence: float, status: GradingStatus = GradingStatus.GRADED) -> GradeResult:
    return GradeResult(
        question_id="q1",
        student_id="s1",
        exam_id="exam-1",
        score=1,
        max_score=1,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=grading_confidence, final_score=grading_confidence),
        status=status,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )


def test_high_confidence_only_grading_source_stays_graded():
    result = ConfidenceEngine().evaluate(_grade_result(95))
    assert result.status == GradingStatus.GRADED
    assert result.confidence.final_score == 95


def test_medium_confidence_still_graded_but_flagged_suggested_tier():
    result = ConfidenceEngine().evaluate(_grade_result(80))
    assert result.status == GradingStatus.GRADED
    assert confidence_tier(result.confidence.final_score) == "suggested"


def test_low_confidence_goes_to_needs_review():
    result = ConfidenceEngine().evaluate(_grade_result(50))
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_boundary_at_exactly_review_threshold_is_graded():
    # ! مرز دقیق ۷۰ باید GRADED باشد (>=)، نه NEEDS_REVIEW
    result = ConfidenceEngine().evaluate(_grade_result(70))
    assert result.status == GradingStatus.GRADED


def test_boundary_just_below_review_threshold_needs_review():
    result = ConfidenceEngine().evaluate(_grade_result(69.9))
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_combines_image_quality_and_extraction_confidence_with_grading_confidence():
    # ? میانگین سه منبع: (60 + 80 + 100) / 3 = 80
    result = ConfidenceEngine().evaluate(
        _grade_result(100), image_quality=60, extraction_confidence=80
    )
    assert result.confidence.final_score == 80
    assert result.confidence.image_quality == 60
    assert result.confidence.extraction_confidence == 80


def test_teacher_overridden_status_is_never_changed_by_engine():
    # ! حتی اگر confidence خیلی پایین باشد، تصمیم معلم دست‌نخورده می‌ماند
    overridden = _grade_result(20, status=GradingStatus.TEACHER_OVERRIDDEN)
    result = ConfidenceEngine().evaluate(overridden)
    assert result.status == GradingStatus.TEACHER_OVERRIDDEN


def test_confidence_tier_boundaries():
    assert confidence_tier(90) == "auto"
    assert confidence_tier(89.9) == "suggested"
    assert confidence_tier(70) == "suggested"
    assert confidence_tier(69.9) == "needs_review"
