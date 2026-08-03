# * ==============================================================================
# *                            ConfidenceEngine
# * ==============================================================================
# ? مسئولیت این کلاس: گرفتن یک GradeResult (که از قبل توسط یک Grader ساخته شده
# ? و فقط grading_confidence آن پر است) و ترکیب آن با منابع دیگر اطمینان
# ? (کیفیت تصویر، اطمینان Extraction) تا یک final_score واحد و یک تصمیم نهایی
# ? (GRADED یا NEEDS_REVIEW) بسازد.
#
# ! این کلاس نباید نمره (score) را تغییر دهد - فقط confidence و status را
# ! بازمحاسبه می‌کند. تغییر نمره فقط کار خود Grader یا معلم (Override) است.
#
# ? در فاز‌های فعلی (قبل از OCR)، همه پاسخ‌ها از ورودی دستی می‌آیند، پس
# ? image_quality و extraction_confidence معمولاً None خواهند بود و ترکیب
# ? عملاً فقط شامل grading_confidence می‌شود. این کلاس از همین حالا برای
# ? زمانی که Extraction Layer (فاز‌های بعد از MVP) این مقادیر را پر کند، آماده است.

from domain.models.enums import GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult

# ? طبق طرح اولیه پروژه:
# ?   >= AUTO_ACCEPT_THRESHOLD          -> تصحیح خودکار با اطمینان بالا
# ?   REVIEW_THRESHOLD..AUTO_ACCEPT     -> نمره پیشنهادی، قابل بررسی
# ?   <  REVIEW_THRESHOLD               -> ارسال به Review Queue
# !
# ! چون در حال حاضر GradingStatus فقط دو حالت عملیاتی دارد (GRADED / NEEDS_REVIEW)،
# ! تمایز سه‌گانه بالا از طریق status اعمال نمی‌شود - status فقط بر اساس
# ! REVIEW_THRESHOLD تعیین می‌شود. تمایز "خودکار" در برابر "پیشنهادی" باید در
# ! لایه نمایش (UI/API پنل معلم) با مقایسه مستقیم confidence.final_score با
# ! AUTO_ACCEPT_THRESHOLD انجام شود؛ confidence_tier() برای همین منظور اضافه شده.
AUTO_ACCEPT_THRESHOLD = 90
REVIEW_THRESHOLD = 70


def confidence_tier(final_confidence: float) -> str:
    """? برای نمایش در پنل معلم - سه سطح توصیفی، مستقل از GradingStatus."""
    if final_confidence >= AUTO_ACCEPT_THRESHOLD:
        return "auto"
    if final_confidence >= REVIEW_THRESHOLD:
        return "suggested"
    return "needs_review"


class ConfidenceEngine:
    def evaluate(
        self,
        grade_result: GradeResult,
        image_quality: float | None = None,
        extraction_confidence: float | None = None,
    ) -> GradeResult:
        """
        ? یک GradeResult جدید (immutable copy) با confidence و status بازمحاسبه‌شده
        ? برمی‌گرداند. grade_result ورودی تغییر نمی‌کند.
        """
        available_components = [
            component
            for component in (image_quality, extraction_confidence, grade_result.confidence.grading_confidence)
            if component is not None
        ]
        # ! grading_confidence همیشه توسط Grader پر می‌شود، پس این لیست هرگز خالی نیست.
        final_confidence = sum(available_components) / len(available_components)

        updated_confidence = ConfidenceScore(
            image_quality=image_quality,
            extraction_confidence=extraction_confidence,
            grading_confidence=grade_result.confidence.grading_confidence,
            final_score=final_confidence,
        )
        new_status = self._determine_status(final_confidence, grade_result.status)

        return grade_result.model_copy(
            update={"confidence": updated_confidence, "status": new_status}
        )

    @staticmethod
    def _determine_status(
        final_confidence: float, current_status: GradingStatus
    ) -> GradingStatus:
        # ! اگر معلم قبلاً این نتیجه را دستی override کرده (TEACHER_OVERRIDDEN)،
        # ! ConfidenceEngine هرگز نباید آن تصمیم را بازنویسی کند.
        if current_status == GradingStatus.TEACHER_OVERRIDDEN:
            return current_status

        if final_confidence >= REVIEW_THRESHOLD:
            return GradingStatus.GRADED
        return GradingStatus.NEEDS_REVIEW
