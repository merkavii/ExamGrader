# * ==============================================================================
# *                       API Request/Response Schemas
# * ==============================================================================
# ? این مدل‌ها با مدل‌های domain/models فرق دارند: اینجا فیلدهایی مثل id و
# ? exam_id وجود ندارند چون سرور آن‌ها را تولید می‌کند، نه معلم.
# ! هرگز مدل‌های Domain را مستقیماً به‌عنوان request body در روترها استفاده نکن -
# ! این باعث می‌شود کلاینت مجبور شود id بسازد که مسئولیت سرور است.

from pydantic import BaseModel

from domain.models.enums import AnswerSource, QuestionType
from domain.models.exam import CorrectAnswer
from domain.models.rubric import Rubric
from domain.models.student import AnswerContent


class ExamCreateRequest(BaseModel):
    title: str


class QuestionCreateRequest(BaseModel):
    question_text: str
    question_type: QuestionType
    correct_answer: CorrectAnswer
    max_score: float
    numeric_tolerance: float | None = None
    rubric: Rubric | None = None
    options: list[str] | None = None


class StudentCreateRequest(BaseModel):
    full_name: str


class StudentAnswerSubmitItem(BaseModel):
    """? یک آیتم پاسخ برای یک سؤال مشخص - بخشی از ثبت کل برگه دانش‌آموز."""

    question_id: str
    answer_content: AnswerContent


class SheetSubmitRequest(BaseModel):
    """? ثبت دستی «کل برگه» یک دانش‌آموز برای یک آزمون - یک یا چند پاسخ با هم."""

    answers: list[StudentAnswerSubmitItem]
    source: AnswerSource = AnswerSource.MANUAL


class SheetStatusResponse(BaseModel):
    """
    ? خلاصه وضعیت یک برگه برای نمایش در جدول Sheets پنل معلم.

    ! در فاز ۱ فقط "چند سؤال پاسخ داده شده" را نشان می‌دهد - وضعیت واقعی
    ! تصحیح (Graded / Needs Review) در فاز ۴ و ۵ اضافه می‌شود.
    """

    student_id: str
    student_full_name: str
    answered_questions: int
    total_questions: int
