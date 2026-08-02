# * ==============================================================================
# *                    LLM-Based Result Builder (Helper)
# * ==============================================================================
# ? مشترک بین EssayGrader و ShortAnswerGrader - هر دو باید بر اساس confidence
# ? خروجی مدل، status را GRADED یا NEEDS_REVIEW تعیین کنند.
#
# ! todo این آستانه ثابت (۷۰) موقتی است. در فاز ۴، ConfidenceEngine باید این
# ! todo منطق را با ترکیب چند منبع اطمینان (نه فقط grading_confidence) جایگزین کند.
# ! todo فعلاً فقط برای این‌که EssayGrader/ShortAnswerGrader به‌تنهایی قابل تست
# ! todo و استفاده باشند، همین‌جا یک تصمیم ساده گرفته شده.

from domain.models.enums import GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult

_PROVISIONAL_REVIEW_THRESHOLD = 70


def build_llm_based_result(
    question_id: str,
    student_id: str,
    exam_id: str,
    score: float,
    max_score: float,
    reasoning: str,
    grading_confidence: float,
    graded_by: str,
) -> GradeResult:
    status = (
        GradingStatus.GRADED
        if grading_confidence >= _PROVISIONAL_REVIEW_THRESHOLD
        else GradingStatus.NEEDS_REVIEW
    )
    return GradeResult(
        question_id=question_id,
        student_id=student_id,
        exam_id=exam_id,
        score=score,
        max_score=max_score,
        reasoning=reasoning,
        confidence=ConfidenceScore(
            grading_confidence=grading_confidence, final_score=grading_confidence
        ),
        status=status,
        graded_by=graded_by,
    )
