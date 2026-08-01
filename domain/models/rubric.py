# * ==============================================================================
# *                                  Rubric
# * ==============================================================================
# ? Rubric معیار دقیق نمره‌دهی سؤال تشریحی یا پاسخ کوتاه معنایی است.
# ? هر Rubric از چند RubricCriterion تشکیل شده که هرکدام امتیاز مستقل خودش را دارد.

from pydantic import BaseModel, Field, field_validator


class RubricCriterion(BaseModel):
    """? یک معیار مشخص از Rubric؛ مثلاً «اشاره به نور: ۱ نمره»."""

    description: str = Field(min_length=1)
    points: float = Field(gt=0)


class Rubric(BaseModel):
    """
    ? مجموعه‌ای از RubricCriterion که جمع امتیازشان باید با max_score سؤال برابر باشد.

    ! این اعتبارسنجی (جمع criteria == max_score) در همین جا انجام نمی‌شود،
    ! چون Rubric از max_score سؤال بی‌خبر است. این بررسی در Question انجام می‌شود
    ! تا Rubric مستقل و قابل استفاده مجدد در سؤال‌های دیگر بماند.
    """

    criteria: list[RubricCriterion] = Field(min_length=1)

    @property
    def total_points(self) -> float:
        return sum(criterion.points for criterion in self.criteria)

    @field_validator("criteria")
    @classmethod
    def ensure_unique_descriptions(
        cls, criteria: list[RubricCriterion]
    ) -> list[RubricCriterion]:
        # ? جلوگیری از دو معیار با توضیح تکراری که باعث سردرگمی در نمایش به معلم می‌شود
        descriptions = [criterion.description for criterion in criteria]
        if len(descriptions) != len(set(descriptions)):
            raise ValueError("Rubric criteria must have unique descriptions")
        return criteria
