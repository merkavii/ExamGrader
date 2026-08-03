# * ==============================================================================
# *                              ReviewQueue
# * ==============================================================================
# ? مسئولیت این کلاس: فیلتر کردن نتایج نیازمند بازبینی از یک مجموعه GradeResult،
# ? و اعمال تصمیم نهایی معلم (Override) روی یک نتیجه مشخص.
#
# ! این کلاس در فاز ۴ به دیتابیس وصل نیست - روی لیستی از GradeResult که در
# ! حافظه (in-memory) به آن داده می‌شود کار می‌کند. اتصال به Repository واقعی
# ! (خواندن/نوشتن GradeResult از دیتابیس) در فاز ۵ اضافه می‌شود - این‌طوری
# ! منطق "چه چیزی نیاز به بازبینی دارد" مستقل از این‌که داده از کجا آمده
# ! (SQL، تست، یا حتی فایل) قابل تست و استفاده مجدد است.

from datetime import datetime, timezone

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import GradeResult


class InvalidOverrideScoreError(Exception):
    """? وقتی معلم نمره‌ای خارج از بازه مجاز [0, max_score] وارد کند."""


class ReviewQueue:
    @staticmethod
    def filter_needing_review(grade_results: list[GradeResult]) -> list[GradeResult]:
        """? فقط نتایجی که هنوز NEEDS_REVIEW هستند را برمی‌گرداند."""
        return [
            result
            for result in grade_results
            if result.status == GradingStatus.NEEDS_REVIEW
        ]

    @staticmethod
    def apply_teacher_override(
        grade_result: GradeResult,
        final_score: float,
        teacher_reasoning: str,
    ) -> GradeResult:
        """
        ? تصمیم نهایی معلم را جایگزین نمره/دلیل AI می‌کند و status را
        ? TEACHER_OVERRIDDEN می‌گذارد - این وضعیت دیگر توسط ConfidenceEngine
        ? یا هیچ Grader ای بازنویسی نمی‌شود (طبق قانون Audit Trail).

        ! نمره معلم باید داخل بازه [0, max_score] باشد - حتی معلم هم نمی‌تواند
        ! از سقف نمره سؤال بیشتر بدهد؛ این یک قانون داده‌ای سخت‌گیرانه است،
        ! نه فقط توصیه.
        """
        if final_score < 0 or final_score > grade_result.max_score:
            raise InvalidOverrideScoreError(
                f"final_score ({final_score}) must be between 0 and "
                f"max_score ({grade_result.max_score})"
            )

        return grade_result.model_copy(
            update={
                "score": final_score,
                "reasoning": teacher_reasoning,
                "status": GradingStatus.TEACHER_OVERRIDDEN,
                "grading_method": GradingMethod.TEACHER,
                "updated_at": datetime.now(timezone.utc),
            }
        )
