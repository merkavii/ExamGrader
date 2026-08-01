# * ==============================================================================
# *                              Domain Enums
# * ==============================================================================
# ? این فایل فقط Enum های پایه دامنه را نگه می‌دارد تا در چند فایل مختلف
# ? (exam.py, student.py, grading_result.py) بدون import چرخه‌ای قابل استفاده باشند.

from enum import Enum


class QuestionType(str, Enum):
    """? نوع سؤال - تعیین‌کننده این‌که کدام Grader مسئول تصحیح آن است."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_IN_BLANK = "fill_in_blank"
    NUMERIC = "numeric"
    MATCHING = "matching"
    ESSAY = "essay"


class AnswerSource(str, Enum):
    """
    ? مشخص می‌کند پاسخ دانش‌آموز از چه روشی وارد سیستم شده است.

    ! این فیلد فقط برای Audit / Confidence استفاده می‌شود.
    ! هیچ Grader ای اجازه ندارد بر اساس این مقدار منطق نمره‌دهی را تغییر دهد؛
    ! تفاوت رفتار فقط باید در لایه Extraction/Normalization اتفاق بیفتد.
    """

    MANUAL = "manual"
    IMAGE = "image"
    PDF = "pdf"
    EXCEL = "excel"
    API = "api"


class GradingStatus(str, Enum):
    """? وضعیت تصحیح یک برگه یا یک پاسخ مشخص - برای نمایش در پنل معلم."""

    NOT_GRADED = "not_graded"
    GRADED = "graded"
    NEEDS_REVIEW = "needs_review"
    TEACHER_OVERRIDDEN = "teacher_overridden"
