# * ==============================================================================
# *                              Exam / Question
# * ==============================================================================
# ? این فایل هسته Canonical Schema سؤال‌ها را تعریف می‌کند.
# ? هر سؤال - چه از ورودی دستی بیاید چه از عکس - در نهایت باید instance ای از
# ? کلاس Question باشد. این تضمین می‌کند Grading Engine هیچ‌وقت به منبع ورودی
# ? وابسته نشود.

import uuid

from pydantic import BaseModel, Field, model_validator

from domain.models.enums import QuestionType
from domain.models.rubric import Rubric


class CorrectAnswer(BaseModel):
    """
    ? پاسخ صحیح یک سؤال. بسته به question_type فقط بخشی از این فیلدها پر می‌شود.

    ! این مدل عمداً یک "Union از همه حالت‌ها" است نه یک کلاس جدا برای هر نوع سؤال،
    ! چون در فاز ۰ فقط ساختار داده را طراحی می‌کنیم. اگر در فازهای بعدی منطق
    ! اعتبارسنجی هر نوع پیچیده‌تر شد، می‌توان به Discriminated Union پدیاntic
    ! مهاجرت کرد بدون این‌که Grader ها را تغییر دهیم (چون فقط از Question.correct_answer
    ! استفاده می‌کنند، نه مستقیماً از این کلاس).
    """

    selected_option: str | None = None          # MULTIPLE_CHOICE, TRUE_FALSE
    text: str | None = None                       # SHORT_ANSWER, FILL_IN_BLANK
    numeric_value: float | None = None            # NUMERIC
    matching_pairs: dict[str, str] | None = None  # MATCHING -> {"1": "A", "2": "B"}
    essay_reference: str | None = None            # ESSAY -> پاسخ نمونه/مرجع برای LLM


class Question(BaseModel):
    """? یک سؤال آزمون با نوع مشخص، پاسخ صحیح و نمره کامل آن سؤال."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exam_id: str
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    correct_answer: CorrectAnswer
    max_score: float = Field(gt=0)

    # ? فقط برای NUMERIC - میزان خطای قابل قبول (مثلاً 9.81 ± 0.05)
    numeric_tolerance: float | None = Field(default=None, ge=0)

    # ? فقط برای ESSAY و در آینده SHORT_ANSWER معنایی
    rubric: Rubric | None = None

    # ? فقط برای MULTIPLE_CHOICE - لیست گزینه‌ها برای نمایش به معلم/دانش‌آموز
    options: list[str] | None = None

    @model_validator(mode="after")
    def validate_fields_match_question_type(self) -> "Question":
        # ! هر شاخه این validator یک قانون معماری را اجرا می‌کند: داده نامعتبر
        # ! هرگز نباید وارد Canonical Schema شود، حتی اگر منبعش ورودی دستی معلم باشد.
        match self.question_type:
            case QuestionType.MULTIPLE_CHOICE:
                if not self.correct_answer.selected_option:
                    raise ValueError("multiple_choice requires correct_answer.selected_option")
                if not self.options or len(self.options) < 2:
                    raise ValueError("multiple_choice requires at least 2 options")
                if self.correct_answer.selected_option not in self.options:
                    raise ValueError("correct_answer.selected_option must be one of options")

            case QuestionType.TRUE_FALSE:
                if self.correct_answer.selected_option not in ("true", "false"):
                    raise ValueError('true_false requires selected_option to be "true" or "false"')

            case QuestionType.SHORT_ANSWER | QuestionType.FILL_IN_BLANK:
                if not self.correct_answer.text:
                    raise ValueError(f"{self.question_type} requires correct_answer.text")

            case QuestionType.NUMERIC:
                if self.correct_answer.numeric_value is None:
                    raise ValueError("numeric requires correct_answer.numeric_value")
                if self.numeric_tolerance is None:
                    raise ValueError("numeric requires numeric_tolerance to be set explicitly")

            case QuestionType.MATCHING:
                if not self.correct_answer.matching_pairs:
                    raise ValueError("matching requires correct_answer.matching_pairs")

            case QuestionType.ESSAY:
                if not self.correct_answer.essay_reference:
                    raise ValueError("essay requires correct_answer.essay_reference")
                if not self.rubric:
                    raise ValueError("essay requires a rubric")
                if abs(self.rubric.total_points - self.max_score) > 1e-6:
                    raise ValueError(
                        f"rubric total_points ({self.rubric.total_points}) "
                        f"must equal max_score ({self.max_score})"
                    )

        return self


class Exam(BaseModel):
    """? مجموعه‌ای از سؤال‌ها به همراه متادیتای آزمون."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1)
    questions: list[Question] = Field(default_factory=list)

    @property
    def total_score(self) -> float:
        return sum(question.max_score for question in self.questions)

    @model_validator(mode="after")
    def validate_questions_belong_to_exam(self) -> "Exam":
        # ! جلوگیری از باگ ظریف: سؤالی که exam_id اش با آزمون فعلی نمی‌خواند
        for question in self.questions:
            if question.exam_id != self.id:
                raise ValueError(
                    f"Question {question.id} has exam_id={question.exam_id}, "
                    f"expected {self.id}"
                )
        return self
