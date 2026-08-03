# * ==============================================================================
# *                          Student / StudentAnswer
# * ==============================================================================

import uuid

from pydantic import BaseModel, Field

from domain.models.enums import AnswerSource


class Student(BaseModel):
    """? دانش‌آموزی که می‌تواند در چند آزمون مختلف شرکت کند."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str = Field(min_length=1)

    # ? کد دانش‌آموزی که معلم/مدرسه تعیین می‌کند - جدا از id داخلی (UUID) که
    # ? برای انسان قابل خواندن/استفاده نیست. اختیاری چون ممکن است معلم چنین
    # ? کدی نداشته باشد.
    student_code: str | None = Field(default=None, min_length=1)

    # ? عضویت در یک کلاس/گروه آموزشی. طراحی فعلی عمداً ساده است: هر دانش‌آموز
    # ! حداکثر یک کلاس فعلی دارد (نه تاریخچه چند ترم/سال). اگر بعداً نیاز به
    # ! نگهداری تاریخچه عضویت در کلاس‌های مختلف شد، باید یک جدول جداگانه
    # ! (مثلاً StudentClassHistory) اضافه شود - این فیلد نباید برای آن منظور
    # ! بازیابی/سوءاستفاده شود.
    class_id: str | None = Field(default=None)


class AnswerContent(BaseModel):
    """
    ? پاسخ خام دانش‌آموز - ساختار آن دقیقاً موازی با CorrectAnswer در exam.py است
    ? تا Grader ها بتوانند این دو را مستقیم با هم مقایسه کنند.
    """

    selected_option: str | None = None
    text: str | None = None
    numeric_value: float | None = None
    matching_pairs: dict[str, str] | None = None


class StudentAnswer(BaseModel):
    """
    ? پاسخ یک دانش‌آموز به یک سؤال مشخص از یک آزمون مشخص.

    ! این کلاس عمداً چیزی درباره "چطور تصحیح شود" نمی‌داند - فقط داده را حمل می‌کند.
    ! source فقط برای audit/confidence استفاده می‌شود، نه برای تغییر منطق تصحیح.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exam_id: str
    student_id: str
    question_id: str
    answer_content: AnswerContent
    source: AnswerSource

    # ? فقط وقتی source != MANUAL معنا دارد - میزان اطمینان لایه Extraction
    # ? به این‌که این answer_content درست از روی تصویر/سند خوانده شده است.
    extraction_confidence: float | None = Field(default=None, ge=0, le=100)
