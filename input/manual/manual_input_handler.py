# * ==============================================================================
# *                          Manual Input Handler
# * ==============================================================================
# ? مسئولیت این ماژول: گرفتن داده‌ای که معلم مستقیماً در فرم تایپ کرده (Request DTO)
# ? و تبدیل آن به Canonical Schema (Question / StudentAnswer در domain/models).
# ?
# ? چرا این لایه جدا از خود Pydantic validation در app/schemas.py است؟
# ? چون اینجا Normalization هم انجام می‌شود (یکسان‌سازی متن، تبدیل ارقام فارسی)
# ? - کاری که مسئولیت خود Schema های ورودی نیست.
#
# ! این ماژول نباید هیچ کاری با تصویر/OCR داشته باشد - آن مسئولیت
# ! extraction/image_extractor.py در فازهای بعدی است. Manual Input Handler فقط
# ! ورودی‌ای را می‌پذیرد که از قبل به‌صورت متن/عدد ساختاریافته از کلاینت آمده.

from domain.models.exam import CorrectAnswer, Question
from domain.models.student import AnswerContent, StudentAnswer
from normalization.text_normalizer import normalize_text


def _normalize_correct_answer(raw: CorrectAnswer) -> CorrectAnswer:
    return CorrectAnswer(
        selected_option=(
            normalize_text(raw.selected_option) if raw.selected_option else None
        ),
        text=normalize_text(raw.text) if raw.text else None,
        numeric_value=raw.numeric_value,
        matching_pairs=raw.matching_pairs,
        essay_reference=(
            normalize_text(raw.essay_reference) if raw.essay_reference else None
        ),
    )


def build_question_from_manual_input(
    exam_id: str,
    question_text: str,
    question_type,
    correct_answer: CorrectAnswer,
    max_score: float,
    numeric_tolerance: float | None = None,
    rubric=None,
    options: list[str] | None = None,
) -> Question:
    """
    ? یک Question معتبر از ورودی دستی معلم می‌سازد.

    ! اعتبارسنجی نهایی (مثلاً "چهارگزینه‌ای باید گزینه صحیح داخل options باشد")
    ! همچنان داخل خود کلاس Question اتفاق می‌افتد - این تابع فقط قبل از آن
    ! متن را نرمال می‌کند، منطق اعتبارسنجی را تکرار نمی‌کند.
    """
    normalized_options = (
        [normalize_text(option) for option in options] if options else None
    )

    return Question(
        exam_id=exam_id,
        question_text=normalize_text(question_text),
        question_type=question_type,
        correct_answer=_normalize_correct_answer(correct_answer),
        max_score=max_score,
        numeric_tolerance=numeric_tolerance,
        rubric=rubric,
        options=normalized_options,
    )


def build_student_answer_from_manual_input(
    exam_id: str,
    student_id: str,
    question_id: str,
    answer_content: AnswerContent,
    source,
) -> StudentAnswer:
    """? یک StudentAnswer معتبر از ورودی دستی (فرم پاسخ‌برگه) می‌سازد."""
    normalized_content = AnswerContent(
        selected_option=(
            normalize_text(answer_content.selected_option)
            if answer_content.selected_option
            else None
        ),
        text=normalize_text(answer_content.text) if answer_content.text else None,
        numeric_value=answer_content.numeric_value,
        matching_pairs=answer_content.matching_pairs,
    )

    return StudentAnswer(
        exam_id=exam_id,
        student_id=student_id,
        question_id=question_id,
        answer_content=normalized_content,
        source=source,
    )
