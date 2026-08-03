# * ==============================================================================
# *                    Rule-Based Result Builder (Helper)
# * ==============================================================================
# ? Grader های قانون‌محور (MC, True/False, Numeric) هر سه یک ویژگی مشترک دارند:
# ? چون منطق‌شان قطعی و بدون ابهام است، همیشه grading_confidence = 100 می‌دهند.
# ? این تابع فقط برای جلوگیری از تکرار همین چند خط در سه فایل مختلف است -
# ? منطق تصحیح داخل خود Grader ها می‌ماند، نه اینجا.

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult


def build_deterministic_result(
    question_id: str,
    student_id: str,
    exam_id: str,
    score: float,
    max_score: float,
    reasoning: str,
    graded_by: str,
) -> GradeResult:
    """
    ? GradeResult برای Grader های قانون‌محور می‌سازد.

    ! چون این Grader ها هیچ ابهامی در تصمیم‌گیری ندارند (یا پاسخ برابر است یا نه)،
    ! status همیشه GRADED است، نه NEEDS_REVIEW. اگر در فازهای بعدی خواستیم مثلاً
    ! "پاسخ خالی" را هم به بازبینی بفرستیم، این تصمیم باید اینجا صریح تغییر کند.
    """
    return GradeResult(
        question_id=question_id,
        student_id=student_id,
        exam_id=exam_id,
        score=score,
        max_score=max_score,
        reasoning=reasoning,
        confidence=ConfidenceScore(grading_confidence=100, final_score=100),
        status=GradingStatus.GRADED,
        grading_method=GradingMethod.RULE_BASED,
        graded_by=graded_by,
    )
