# * ==============================================================================
# *                      GradeResult / ConfidenceScore
# * ==============================================================================
# ? خروجی استاندارد و مشترک همه Grader ها - مستقل از نوع سؤال.
# ? هر Grader (چه قانون‌محور، چه LLM-based) باید دقیقاً همین ساختار را برگرداند.

from pydantic import BaseModel, Field, model_validator

from domain.models.enums import GradingStatus


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

    question_id: str
    student_id: str
    exam_id: str
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    reasoning: str = Field(min_length=1)
    confidence: ConfidenceScore
    status: GradingStatus
    graded_by: str = Field(min_length=1)  # ? نام Grader، برای audit - مثلاً "MultipleChoiceGrader"

    @model_validator(mode="after")
    def validate_score_within_bounds(self) -> "GradeResult":
        if self.score > self.max_score:
            raise ValueError(
                f"score ({self.score}) cannot exceed max_score ({self.max_score})"
            )
        return self
