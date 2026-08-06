# * ==============================================================================
# *                          Empty Answer Detection
# * ==============================================================================
# ? تنها منبع تشخیص "پاسخ خالی" در کل پروژه. قبل از این فایل، این تشخیص در هر
# ? Grader جداگانه و ناهماهنگ تکرار شده بود - بعضی فقط None را می‌گرفتند، هیچ‌کدام
# ? whitespace خالص را درست تشخیص نمی‌دادند. GradingOrchestrator اکنون این تابع
# ? را قبل از انتخاب/فراخوانی هر Grader صدا می‌زند - یعنی قبل از هر تماس احتمالی
# ? با LLM.
#
# ! هیچ Grader یا لایه دیگری نباید این منطق را دوباره پیاده کند. اگر نوع سؤال
# ! جدیدی (مثلاً Matching) اضافه شد، تعریف "خالی بودن" آن باید همین‌جا اضافه شود.

from domain.models.enums import QuestionType
from domain.models.student import AnswerContent


def is_blank_text(value: str | None) -> bool:
    """? None، رشته خالی ""، یا رشته‌ای فقط شامل whitespace را خالی می‌داند."""
    return value is None or value.strip() == ""


def is_answer_empty(question_type: QuestionType, answer_content: AnswerContent) -> bool:
    """
    ? بر اساس نوع سؤال، فقط فیلد مربوطه از answer_content بررسی می‌شود - چون هر
    ? نوع سؤال فقط یک فیلد از AnswerContent را معنادار می‌داند.
    """
    match question_type:
        case QuestionType.MULTIPLE_CHOICE | QuestionType.TRUE_FALSE:
            return is_blank_text(answer_content.selected_option)
        case QuestionType.NUMERIC:
            return answer_content.numeric_value is None
        case QuestionType.SHORT_ANSWER | QuestionType.FILL_IN_BLANK | QuestionType.ESSAY:
            return is_blank_text(answer_content.text)
        case QuestionType.MATCHING:
            return not answer_content.matching_pairs

    return False  # ! نوع ناشناخته - محافظه‌کارانه "خالی نیست" فرض می‌شود
