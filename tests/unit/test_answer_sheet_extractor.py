# * ==============================================================================
# *                    Tests: AnswerSheetExtractor
# * ==============================================================================
# ? این تست‌ها با FakeOCRClient اجرا می‌شوند - چون منطقی که اینجا تست می‌شود
# ? (نگاشت ترتیبی خط->سؤال، تفسیر متن بر اساس نوع سؤال) کاملاً مستقل از این
# ? است که OCR واقعی از کجا آمده.

import cv2
import numpy as np
import pytest

from domain.models.enums import QuestionType
from domain.models.exam import CorrectAnswer, Question
from extraction.answer_sheet_extractor import AnswerSheetExtractor
from ocr.ocr_client import OCRLine
from tests.unit.fakes import FakeOCRClient


def _encode_blank_image() -> bytes:
    # ? یک تصویر ساده و معتبر برای عبور از مرحله imdecode/quality-check -
    # ? خود متن این تصویر اهمیتی ندارد چون FakeOCRClient واقعاً آن را نمی‌خواند.
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    return cv2.imencode(".png", image)[1].tobytes()


def _question(question_type: QuestionType, **kwargs) -> Question:
    defaults = {
        "id": kwargs.pop("id", "q1"),
        "exam_id": "exam-1",
        "question_text": "سؤال نمونه",
        "question_type": question_type,
        "max_score": 1,
    }
    defaults.update(kwargs)
    return Question(**defaults)


def test_maps_lines_to_questions_in_order():
    questions = [
        _question(QuestionType.SHORT_ANSWER, id="q1", correct_answer=CorrectAnswer(text="تهران")),
        _question(QuestionType.SHORT_ANSWER, id="q2", correct_answer=CorrectAnswer(text="اصفهان")),
    ]
    ocr = FakeOCRClient(
        lines=[OCRLine(text="تهران", confidence=90), OCRLine(text="اصفهان", confidence=85)]
    )
    extractor = AnswerSheetExtractor(ocr)

    result = extractor.extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].question_id == "q1"
    assert result.extracted_answers[0].suggested_answer.text == "تهران"
    assert result.extracted_answers[1].suggested_answer.text == "اصفهان"


def test_fewer_ocr_lines_than_questions_leaves_remaining_unanswered():
    questions = [
        _question(QuestionType.SHORT_ANSWER, id="q1", correct_answer=CorrectAnswer(text="تهران")),
        _question(QuestionType.SHORT_ANSWER, id="q2", correct_answer=CorrectAnswer(text="اصفهان")),
    ]
    ocr = FakeOCRClient(lines=[OCRLine(text="تهران", confidence=90)])
    extractor = AnswerSheetExtractor(ocr)

    result = extractor.extract(_encode_blank_image(), questions)

    assert len(result.extracted_answers) == 2
    assert result.extracted_answers[1].suggested_answer.text is None
    assert result.extracted_answers[1].extraction_confidence == 0


def test_multiple_choice_matches_against_options():
    questions = [
        _question(
            QuestionType.MULTIPLE_CHOICE,
            correct_answer=CorrectAnswer(selected_option="زمین"),
            options=["ماه", "زمین"],
        )
    ]
    ocr = FakeOCRClient(lines=[OCRLine(text="زمین", confidence=88)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].suggested_answer.selected_option == "زمین"
    assert result.extracted_answers[0].extraction_confidence > 30  # تفسیر موفق بود


def test_multiple_choice_unmatched_option_gets_low_confidence():
    # ! متنی که با هیچ گزینه‌ای مطابقت ندارد - حتی اگر OCR به آن مطمئن بود
    questions = [
        _question(
            QuestionType.MULTIPLE_CHOICE,
            correct_answer=CorrectAnswer(selected_option="زمین"),
            options=["ماه", "زمین"],
        )
    ]
    ocr = FakeOCRClient(lines=[OCRLine(text="مریخ", confidence=95)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].suggested_answer.selected_option is None
    assert result.extracted_answers[0].extraction_confidence <= 30


def test_true_false_recognizes_persian_words():
    questions = [_question(QuestionType.TRUE_FALSE, correct_answer=CorrectAnswer(selected_option="true"))]
    ocr = FakeOCRClient(lines=[OCRLine(text="درست", confidence=80)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)
    assert result.extracted_answers[0].suggested_answer.selected_option == "true"


def test_numeric_parses_persian_digits():
    questions = [
        _question(
            QuestionType.NUMERIC,
            correct_answer=CorrectAnswer(numeric_value=9.81),
            numeric_tolerance=0.05,
        )
    ]
    # ? رقم فارسی - باید توسط normalization/number_normalizer.py موجود پردازش شود
    ocr = FakeOCRClient(lines=[OCRLine(text="۹.۸۱", confidence=91)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].suggested_answer.numeric_value == 9.81


def test_numeric_unparseable_text_gets_low_confidence():
    questions = [
        _question(
            QuestionType.NUMERIC, correct_answer=CorrectAnswer(numeric_value=9.81), numeric_tolerance=0.05
        )
    ]
    ocr = FakeOCRClient(lines=[OCRLine(text="نامشخص", confidence=90)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].suggested_answer.numeric_value is None
    assert result.extracted_answers[0].extraction_confidence <= 30


def test_strips_question_number_prefix_before_parsing():
    questions = [_question(QuestionType.SHORT_ANSWER, correct_answer=CorrectAnswer(text="تهران"))]
    ocr = FakeOCRClient(lines=[OCRLine(text="Q1: تهران", confidence=85)])
    result = AnswerSheetExtractor(ocr).extract(_encode_blank_image(), questions)

    assert result.extracted_answers[0].suggested_answer.text == "تهران"


def test_low_image_quality_reduces_confidence_even_with_confident_ocr():
    # ? تصویر واقعاً تار/تیره ساخته می‌شود (نه Fake) تا ImageQualityChecker
    # ? واقعی روی آن اجرا شود - فقط OCRClient جعلی است.
    dark_blurry_image = np.full((100, 100, 3), 10, dtype=np.uint8)
    image_bytes = cv2.imencode(".png", dark_blurry_image)[1].tobytes()

    questions = [_question(QuestionType.SHORT_ANSWER, correct_answer=CorrectAnswer(text="تهران"))]
    ocr = FakeOCRClient(lines=[OCRLine(text="تهران", confidence=99)])
    result = AnswerSheetExtractor(ocr).extract(image_bytes, questions)

    # ! با اینکه OCR ادعای اطمینان ۹۹ دارد، چون کیفیت تصویر پایین است،
    # ! اطمینان نهایی باید به‌طور محسوسی کمتر از ۹۹ باشد.
    assert result.extracted_answers[0].extraction_confidence < 60
    assert len(result.quality_issues) > 0
