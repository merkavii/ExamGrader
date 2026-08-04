# * ==============================================================================
# *                       Tests: ScoreAggregator
# * ==============================================================================

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult
from grading.aggregator import ScoreAggregator


def _result(score: float, max_score: float, status: GradingStatus = GradingStatus.GRADED) -> GradeResult:
    return GradeResult(
        question_id="q",
        student_id="s1",
        exam_id="exam-1",
        score=score,
        max_score=max_score,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=90, final_score=90),
        status=status,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )


def test_aggregate_sums_scores_correctly():
    results = [_result(2, 2), _result(0, 1), _result(1, 1)]
    summary = ScoreAggregator.aggregate("s1", "exam-1", results)

    assert summary.total_score == 3
    assert summary.max_total_score == 4
    assert summary.percentage == 75.0
    assert summary.graded_question_count == 3


def test_aggregate_counts_needs_review_items():
    results = [
        _result(1, 1, status=GradingStatus.GRADED),
        _result(0, 1, status=GradingStatus.NEEDS_REVIEW),
    ]
    summary = ScoreAggregator.aggregate("s1", "exam-1", results)
    assert summary.needs_review_question_count == 1


def test_aggregate_handles_empty_results_without_division_by_zero():
    summary = ScoreAggregator.aggregate("s1", "exam-1", [])
    assert summary.total_score == 0
    assert summary.max_total_score == 0
    assert summary.percentage == 0
