# * ==============================================================================
# *                    GradeResultRepository (Interface)
# * ==============================================================================
# ? قرارداد ذخیره‌سازی نتایج تصحیح. پیاده‌سازی واقعی در
# ? infrastructure/repositories/sql_grade_result_repository.py قرار دارد.
#
# ! save() باید idempotent باشد: اگر GradeResult ای برای همان
# ! (exam_id, student_id, question_id) از قبل وجود داشته باشد، باید آن را
# ! به‌روزرسانی کند نه این‌که رکورد تکراری بسازد - این دقیقاً همان چیزی است
# ! که امکان "تصحیح مجدد یک برگه" را بدون تکثیر داده ممکن می‌کند.

from typing import Protocol

from domain.models.grading_result import GradeResult


class GradeResultRepository(Protocol):
    def save(self, grade_result: GradeResult) -> None: ...

    def get_by_id(self, grade_result_id: str) -> GradeResult | None: ...

    def get_by_exam(self, exam_id: str) -> list[GradeResult]: ...

    def get_by_student_and_exam(
        self, student_id: str, exam_id: str
    ) -> list[GradeResult]: ...

    def get_by_student(self, student_id: str) -> list[GradeResult]: ...

    def list_all(self) -> list[GradeResult]: ...
