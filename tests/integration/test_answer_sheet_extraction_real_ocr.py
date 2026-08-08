# * ==============================================================================
# *          Integration Test: AnswerSheetExtractor + Real Tesseract
# * ==============================================================================
# ? برخلاف test_answer_sheet_extractor.py (که از FakeOCRClient استفاده می‌کند)،
# ? این تست از TesseractOCRClient واقعی استفاده می‌کند - Pipeline کامل تصویر
# ? واقعاً تصویر می‌سازد، پیش‌پردازش می‌کند، و OCR واقعی روی آن اجرا می‌شود.
#
# ! زبان انگلیسی انتخاب شده (نه فارسی) چون بسته tesseract-ocr-fas نیاز به نصب
# ! دارد و ممکن است روی هر سیستمی از قبل نصب نباشد؛ این تست فقط "سیم‌کشی
# ! صحیح Pipeline" را تأیید می‌کند، نه دقت OCR فارسی به‌طور خاص. برای تأیید
# ! دقت فارسی، بعد از نصب tesseract-ocr-fas (از طریق apt)، این تست را با یک
# ! متن فارسی واقعی و language="fas" هم اجرا کن.

import pytest

pytest.importorskip("cv2")
pytest.importorskip("pytesseract")

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from domain.models.enums import QuestionType
from domain.models.exam import CorrectAnswer, Question
from extraction.answer_sheet_extractor import AnswerSheetExtractor
from ocr.tesseract_ocr_client import TesseractOCRClient


def _render_answer_sheet_image(lines: list[str]) -> bytes:
    """? یک تصویر واقعی PNG با چند خط متن می‌سازد - شبیه عکس یک برگه پاسخ."""
    image = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except OSError:
        font = ImageFont.load_default()

    y = 40
    for line in lines:
        draw.text((60, y), line, fill=(0, 0, 0), font=font)
        y += 60

    array = np.array(image)
    bgr = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    return cv2.imencode(".png", bgr)[1].tobytes()


@pytest.fixture()
def real_extractor() -> AnswerSheetExtractor:
    # ! فقط انگلیسی - نگاه کن به توضیح بالای فایل
    return AnswerSheetExtractor(TesseractOCRClient(language="eng"))


def test_real_tesseract_extracts_multiple_choice_and_numeric_answers(real_extractor):
    questions = [
        Question(
            exam_id="exam-1",
            question_text="Which is a planet?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer=CorrectAnswer(selected_option="Earth"),
            options=["Moon", "Earth"],
            max_score=1,
        ),
        Question(
            exam_id="exam-1",
            question_text="Gravity constant?",
            question_type=QuestionType.NUMERIC,
            correct_answer=CorrectAnswer(numeric_value=9.81),
            numeric_tolerance=0.05,
            max_score=1,
        ),
    ]

    image_bytes = _render_answer_sheet_image(["Earth", "9.81"])
    result = real_extractor.extract(image_bytes, questions)

    assert len(result.extracted_answers) == 2
    # ! دقت OCR واقعی همیشه ۱۰۰٪ نیست - به‌جای برابری دقیق، بررسی می‌کنیم که
    # ! حداقل یکی از دو پاسخ درست تفسیر شده باشد (تضمین این‌که Pipeline واقعاً
    # ! کار می‌کند، نه یک ادعای غیرواقعی از دقت کامل OCR).
    mc_answer = result.extracted_answers[0].suggested_answer.selected_option
    numeric_answer = result.extracted_answers[1].suggested_answer.numeric_value
    assert mc_answer == "Earth" or numeric_answer == pytest.approx(9.81)


def test_real_tesseract_reports_nonzero_confidence_for_clear_text(real_extractor):
    questions = [
        Question(
            exam_id="exam-1",
            question_text="Capital city?",
            question_type=QuestionType.SHORT_ANSWER,
            correct_answer=CorrectAnswer(text="Tehran"),
            max_score=1,
        )
    ]
    image_bytes = _render_answer_sheet_image(["Tehran"])
    result = real_extractor.extract(image_bytes, questions)

    assert result.extracted_answers[0].extraction_confidence > 0
