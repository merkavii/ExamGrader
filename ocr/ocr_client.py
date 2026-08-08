# * ==============================================================================
# *                              OCRClient (Interface)
# * ==============================================================================
# ? دقیقاً همان الگوی ai/llm_client.py: هیچ لایه بالادستی نباید مستقیماً از
# ? Tesseract یا هر موتور OCR دیگری نام ببرد. اگر فردا خواستیم به یک سرویس
# ? OCR ابری یا مدل دیگری مهاجرت کنیم، فقط یک پیاده‌سازی جدید از این Interface
# ? لازم است.

from abc import ABC, abstractmethod

from pydantic import BaseModel


class OCRLine(BaseModel):
    """? یک خط متن تشخیص‌داده‌شده به همراه اطمینان مخصوص همان خط."""

    text: str
    confidence: float  # ? بین ۰ تا ۱۰۰ - میانگین اطمینان فقط کلمات همین خط


class OCRResult(BaseModel):
    """
    ? خروجی استاندارد یک موتور OCR.

    ! lines عمداً نگه داشته می‌شود (نه فقط یک متن مسطح) چون AnswerSheetExtractor
    ! برای تطبیق ترتیبی «خط N -> سؤال N» به مرز خطوط نیاز دارد؛ اگر همه‌چیز را
    ! به یک رشته flatten می‌کردیم، این مرزبندی برای همیشه از بین می‌رفت.
    """

    lines: list[OCRLine]
    overall_confidence: float  # ? میانگین کلی - برای گزارش سریع کیفیت کل تصویر


class OCRClient(ABC):
    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """
        ? بایت‌های خام یک تصویر (already پردازش‌شده توسط ImagePreprocessor) را
        ? می‌گیرد و متن (به تفکیک خط) + اطمینان هر خط را برمی‌گرداند.

        ! این متد نباید هیچ تفسیری از معنای متن (کدام سؤال، کدام پاسخ) داشته
        ! باشد - آن مسئولیت AnswerSheetExtractor است، نه این لایه.
        """
        raise NotImplementedError
