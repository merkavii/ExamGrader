# * ==============================================================================
# *          Tests: GradingMethod Provenance (rule-based / LLM / teacher)
# * ==============================================================================
# ? این فایل مستقیماً همان نکته‌ای را تست می‌کند که کاربر صراحتاً درخواست کرد:
# ? مشخص بودن این‌که نمره فعلی یک GradeResult توسط چه چیزی ثبت شده است.

from domain.models.enums import GradingMethod
from grading.llm_based_result import build_llm_based_result
from grading.rule_based_result import build_deterministic_result


def test_rule_based_builder_sets_rule_based_method():
    result = build_deterministic_result(
        question_id="q1",
        student_id="s1",
        exam_id="exam-1",
        score=1,
        max_score=1,
        reasoning="پاسخ صحیح بود",
        graded_by="TrueFalseGrader",
    )
    assert result.grading_method == GradingMethod.RULE_BASED


def test_llm_based_builder_sets_llm_method():
    result = build_llm_based_result(
        question_id="q1",
        student_id="s1",
        exam_id="exam-1",
        score=1,
        max_score=1,
        reasoning="پاسخ از نظر معنایی درست بود",
        grading_confidence=90,
        graded_by="ShortAnswerGrader",
    )
    assert result.grading_method == GradingMethod.LLM


# ! تست grading_method == TEACHER بعد از Override، در
# ! tests/unit/test_review_queue.py پوشش داده شده (چون به ReviewQueue وابسته است).
