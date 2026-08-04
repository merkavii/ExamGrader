# * ==============================================================================
# *                   SqlGradeResultRepository (Implementation)
# * ==============================================================================
# ? پیاده‌سازی واقعی GradeResultRepository با SQLAlchemy/SQLite.
#
# ! save() قبل از insert، بررسی می‌کند آیا رکوردی برای همین
# ! (exam_id, student_id, question_id) از قبل وجود دارد یا نه - اگر داشت،
# ! آپدیت می‌کند (Upsert)، نه insert جدید. این دقیقاً همان منطقی است که در
# ! ابتدای پروژه برای "تصحیح مجدد یک برگه بدون تکثیر داده" لازم بود.

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models.grading_result import GradeResult
from infrastructure.database.mappers import grade_result_from_orm, grade_result_to_orm
from infrastructure.database.models import GradeResultORM


class SqlGradeResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, grade_result: GradeResult) -> None:
        existing = self._session.scalars(
            select(GradeResultORM).where(
                GradeResultORM.exam_id == grade_result.exam_id,
                GradeResultORM.student_id == grade_result.student_id,
                GradeResultORM.question_id == grade_result.question_id,
            )
        ).first()

        if existing:
            # ? آپدیت درجا روی رکورد موجود - همان ردیف overwrite می‌شود، نه
            # ? رکورد جدید. id اصلی (اولین بار که تصحیح شد) حفظ می‌شود.
            existing.score = grade_result.score
            existing.max_score = grade_result.max_score
            existing.reasoning = grade_result.reasoning
            existing.confidence = grade_result.confidence.model_dump()
            existing.status = grade_result.status.value
            existing.grading_method = grade_result.grading_method.value
            existing.graded_by = grade_result.graded_by
            existing.updated_at = grade_result.updated_at
        else:
            self._session.add(grade_result_to_orm(grade_result))

        self._session.commit()

    def get_by_id(self, grade_result_id: str) -> GradeResult | None:
        orm_result = self._session.get(GradeResultORM, grade_result_id)
        return grade_result_from_orm(orm_result) if orm_result else None

    def get_by_exam(self, exam_id: str) -> list[GradeResult]:
        orm_results = self._session.scalars(
            select(GradeResultORM).where(GradeResultORM.exam_id == exam_id)
        ).all()
        return [grade_result_from_orm(r) for r in orm_results]

    def get_by_student_and_exam(
        self, student_id: str, exam_id: str
    ) -> list[GradeResult]:
        orm_results = self._session.scalars(
            select(GradeResultORM).where(
                GradeResultORM.student_id == student_id,
                GradeResultORM.exam_id == exam_id,
            )
        ).all()
        return [grade_result_from_orm(r) for r in orm_results]

    def list_all(self) -> list[GradeResult]:
        orm_results = self._session.scalars(select(GradeResultORM)).all()
        return [grade_result_from_orm(r) for r in orm_results]
