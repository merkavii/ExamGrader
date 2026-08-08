# * ==============================================================================
# *                          AnswerSheetExtractor
# * ==============================================================================
# ? هماهنگ‌کننده کل مسیر: تصویر خام -> بررسی کیفیت -> پیش‌پردازش -> OCR ->
# ? نگاشت هر خط به یک سؤال (بر اساس ترتیب) -> AnswerContent پیشنهادی.
#
# ! این کلاس هرگز چیزی را در دیتابیس ذخیره نمی‌کند و GradeResult نمی‌سازد -
# ! فقط "پیشنهاد" تولید می‌کند که معلم باید قبل از ثبت نهایی ببیند/ویرایش کند
# ! (دقیقاً طبق قانون اولیه پروژه: "معلم باید بتواند اطلاعات استخراج‌شده را
# ! قبل از ذخیره بررسی و ویرایش کند").
#
# ! محدودیت شناخته‌شده و عمدی این فاز: نگاشت هر خط استخراج‌شده به سؤال متناظر
# ! صرفاً بر اساس ترتیب (خط N -> سؤال N-ام) انجام می‌شود، نه تحلیل چیدمان
# ! واقعی صفحه. تحلیل چیدمان (layout understanding) پیچیدگی قابل‌توجهی دارد و
# ! عمداً به فاز بعدی موکول شده - همان اصل "تا جای ممکن از روش قطعی استفاده
# ! کن" که از ابتدای پروژه دنبال شده است.

import re

import cv2
import numpy as np
from pydantic import BaseModel

from domain.models.exam import Question
from domain.models.student import AnswerContent
from extraction.image_quality.preprocessing_pipeline import ImagePreprocessor
from extraction.image_quality.quality_checker import ImageQualityChecker
from normalization.number_normalizer import parse_number
from normalization.text_normalizer import normalize_text
from ocr.ocr_client import OCRClient

# ? اگر متن استخراج‌شده به‌درستی برای نوع سؤال قابل تفسیر نباشد (مثلاً عدد
# ? نامعتبر، یا گزینه‌ای که با هیچ‌کدام از options مطابقت ندارد)، حتی اگر خود
# ? OCR به متنش مطمئن بود، اطمینان نهایی این پاسخ به این سقف پایین محدود می‌شود
# ? - چون داشتن متن واضحِ نامربوط، بهتر از نداشتن متن نیست.
UNPARSEABLE_CONFIDENCE_CAP = 30.0

# ? الگوی پیشوندهایی مثل "Q1:"، "سؤال ۲-" که دانش‌آموزان معمولاً قبل از پاسخ
# ? می‌نویسند - قبل از تفسیر پاسخ حذف می‌شوند تا در تشخیص گزینه/عدد اختلال ایجاد نکنند.
_QUESTION_PREFIX_PATTERN = re.compile(
    r"^\s*(?:[Qq]\s*\d+|سؤال\s*\d+|سوال\s*\d+)\s*[:\.\-\)]\s*"
)

_TRUE_FALSE_MAP = {
    "true": "true", "false": "false",
    "درست": "true", "غلط": "false", "صحیح": "true", "نادرست": "false",
}


class ExtractedAnswer(BaseModel):
    """? یک پیشنهاد استخراج‌شده برای یک سؤال مشخص - فقط برای نمایش/بررسی معلم."""

    question_id: str
    raw_text: str  # ? دقیقاً همان چیزی که OCR خوانده - برای شفافیت به معلم نشان داده می‌شود
    suggested_answer: AnswerContent
    extraction_confidence: float  # ? ۰ تا ۱۰۰ - ترکیب اطمینان OCR و موفقیت تفسیر


class AnswerSheetExtractionResult(BaseModel):
    image_quality_score: float
    quality_issues: list[str]
    extracted_answers: list[ExtractedAnswer]


class AnswerSheetExtractor:
    def __init__(self, ocr_client: OCRClient) -> None:
        self._ocr_client = ocr_client
        self._quality_checker = ImageQualityChecker()
        self._preprocessor = ImagePreprocessor()

    def extract(
        self, image_bytes: bytes, questions: list[Question]
    ) -> AnswerSheetExtractionResult:
        raw_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(raw_array, cv2.IMREAD_COLOR)

        quality_report = self._quality_checker.check(image)

        # ! حتی با کیفیت پایین، ادامه می‌دهیم (رد نمی‌کنیم) - ولی quality_score
        # ! پایین در نهایت روی extraction_confidence هر پاسخ اثر می‌گذارد تا
        # ! معلم متوجه شود این پیشنهادها چندان قابل‌اعتماد نیستند. تصمیم قطعی
        # ! رد/قبول با معلم است، نه سیستم.
        processed_image = self._preprocessor.process(image)
        encoded_success, encoded_image = cv2.imencode(".png", processed_image)
        ocr_result = self._ocr_client.extract_text(encoded_image.tobytes())

        extracted_answers = [
            self._build_extracted_answer(
                question=question,
                line_text=ocr_result.lines[index].text if index < len(ocr_result.lines) else "",
                line_confidence=(
                    ocr_result.lines[index].confidence if index < len(ocr_result.lines) else 0.0
                ),
                image_quality_score=quality_report.quality_score,
            )
            for index, question in enumerate(questions)
        ]

        return AnswerSheetExtractionResult(
            image_quality_score=quality_report.quality_score,
            quality_issues=quality_report.issues,
            extracted_answers=extracted_answers,
        )

    def _build_extracted_answer(
        self,
        question: Question,
        line_text: str,
        line_confidence: float,
        image_quality_score: float,
    ) -> ExtractedAnswer:
        cleaned_text = _QUESTION_PREFIX_PATTERN.sub("", line_text).strip()
        normalized_text = normalize_text(cleaned_text) if cleaned_text else ""

        answer_content, parsed_successfully = self._parse_for_question_type(
            question, normalized_text
        )

        # ? اطمینان نهایی: میانگین کیفیت تصویر و اطمینان OCR همین خط، مگر
        # ? این‌که تفسیر شکست خورده باشد که در آن صورت به سقف پایین محدود می‌شود.
        combined_confidence = (image_quality_score + line_confidence) / 2
        final_confidence = (
            combined_confidence
            if parsed_successfully
            else min(combined_confidence, UNPARSEABLE_CONFIDENCE_CAP)
        )

        return ExtractedAnswer(
            question_id=question.id,
            raw_text=line_text,
            suggested_answer=answer_content,
            extraction_confidence=round(final_confidence, 2),
        )

    @staticmethod
    def _parse_for_question_type(
        question: Question, text: str
    ) -> tuple[AnswerContent, bool]:
        if not text:
            return AnswerContent(), False

        match question.question_type:
            case "multiple_choice":
                for option in question.options or []:
                    if normalize_text(option) == text:
                        return AnswerContent(selected_option=option), True
                return AnswerContent(), False

            case "true_false":
                mapped = _TRUE_FALSE_MAP.get(text.lower())
                if mapped:
                    return AnswerContent(selected_option=mapped), True
                return AnswerContent(), False

            case "numeric":
                try:
                    return AnswerContent(numeric_value=parse_number(text)), True
                except ValueError:
                    return AnswerContent(), False

            case "short_answer" | "fill_in_blank" | "essay":
                # ? برای پاسخ متنی، هر چیزی که OCR خوانده «قابل تفسیر» است -
                # ? درست/غلط بودنش کار Grader است، نه این لایه.
                return AnswerContent(text=text), True

            case _:
                return AnswerContent(), False
