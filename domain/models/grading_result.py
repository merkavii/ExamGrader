# * ==============================================================================
# *                      GradeResult / ConfidenceScore
# * ==============================================================================
# ? خروجی استاندارد و مشترک همه Grader ها - مستقل از نوع سؤال.
# ? هر Grader (چه قانون‌محور، چه LLM-based) باید دقیقاً همین ساختار را برگرداند.

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from domain.models.enums import GradingMethod, GradingStatus


class ConfidenceScore(BaseModel):
    """
    ? ترکیب چند منبع اطمینان مختلف در طول pipeline.

    ? فرمول دقیق ترکیب (وزن هرکدام) در فاز ۴ (Confidence Engine) طراحی می‌شود؛
    ? اینجا فقط ساختار داده مشخص شده است.
    """

    image_quality: float | None = Field(default=None, ge=0, le=100)
    extraction_confidence: float | None = Field(default=None, ge=0, le=100)
    grading_confidence: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)


class GradeResult(BaseModel):
    """
    ? خروجی نهایی تصحیح یک (Question, StudentAnswer) مشخص.

    ! reasoning هرگز نباید خالی باشد - حتی Grader های قانون‌محور (مثل چهارگزینه‌ای)
    ! باید دلیل نمره را به زبان قابل‌فهم بنویسند (مثلاً "پاسخ دانش‌آموز B بود،
    ! پاسخ صحیح A است"). این برای شفافیت پنل بازبینی معلم ضروری است.
    """

    # ? id مستقل از (exam_id, student_id, question_id) نگه داشته می‌شود تا با
    # ? الگوی بقیه جدول‌های پروژه (Exam, Question, Student, ...) یکسان بماند؛
    # ? یکتایی واقعی این سه‌تایی در لایه Repository/دیتابیس با UNIQUE constraint
    # ? تضمین می‌شود، نه با استفاده از آن‌ها به‌عنوان Primary Key مرکب.
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    student_id: str
    exam_id: str
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    reasoning: str = Field(min_length=1)
    confidence: ConfidenceScore
    status: GradingStatus

    # ? مشخص می‌کند نمره فعلی از کجا آمده - قانون‌محور/LLM/معلم.
    # ! این فیلد الزامی است (بدون مقدار پیش‌فرض) تا هر مسیری که GradeResult
    # ! می‌سازد یا تغییر می‌دهد (build_deterministic_result, build_llm_based_result,
    # ! ReviewQueue.apply_teacher_override) مجبور باشد صراحتاً آن را مشخص کند.
    grading_method: GradingMethod

    graded_by: str = Field(min_length=1)  # ? نام Grader، برای audit - مثلاً "MultipleChoiceGrader"

    # ? برای تحلیل‌های آینده (روند پیشرفت، تاریخچه) - زمان اولین تصحیح و آخرین تغییر.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)

    @model_validator(mode="after")
    def validate_score_within_bounds(self) -> "GradeResult":
        if self.score > self.max_score:
            raise ValueError(
                f"score ({self.score}) cannot exceed max_score ({self.max_score})"
            )
        return self
