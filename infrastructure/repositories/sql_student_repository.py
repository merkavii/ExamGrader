# * ==============================================================================
# *                  SqlStudentRepository (Implementation)
# * ==============================================================================

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models.student import Student, StudentAnswer
from infrastructure.database.mappers import (
    student_answer_from_orm,
    student_answer_to_orm,
    student_from_orm,
    student_to_orm,
)
from infrastructure.database.models import StudentAnswerORM, StudentORM


class SqlStudentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, student: Student) -> None:
        existing = self._session.get(StudentORM, student.id)
        if existing:
            existing.full_name = student.full_name
            existing.student_code = student.student_code
            existing.class_id = student.class_id
        else:
            self._session.add(student_to_orm(student))
        self._session.commit()

    def get_by_id(self, student_id: str) -> Student | None:
        orm_student = self._session.get(StudentORM, student_id)
        return student_from_orm(orm_student) if orm_student else None

    def list_by_exam(self, exam_id: str) -> list[Student]:
        # ? دانش‌آموزانی که حداقل یک پاسخ برای این آزمون ثبت کرده‌اند.
        # ! این یعنی "شرکت‌کننده در آزمون" با join روی student_answers تعریف می‌شود،
        # ! نه یک رابطه مستقیم Student <-> Exam (چون Student موجودیت مستقل است).
        student_ids = self._session.scalars(
            select(StudentAnswerORM.student_id)
            .where(StudentAnswerORM.exam_id == exam_id)
            .distinct()
        ).all()
        orm_students = self._session.scalars(
            select(StudentORM).where(StudentORM.id.in_(student_ids))
        ).all()
        return [student_from_orm(s) for s in orm_students]

    def list_by_class(self, class_id: str) -> list[Student]:
        # ? برای نمایش «دانش‌آموزان این کلاس» - این چیزی است که در Class Detail
        # ? پنل معلم لازم است (طبق درخواست: کلاس یا گروه آموزشی).
        orm_students = self._session.scalars(
            select(StudentORM).where(StudentORM.class_id == class_id)
        ).all()
        return [student_from_orm(s) for s in orm_students]

    def list_all(self) -> list[Student]:
        orm_students = self._session.scalars(select(StudentORM)).all()
        return [student_from_orm(s) for s in orm_students]

    def get_many_by_ids(self, student_ids: list[str]) -> list[Student]:
        # ? یک Query با IN(...) به‌جای N Query جدا - همان چیزی که برای صف
        # ? بازبینی غنی‌شده لازم است.
        if not student_ids:
            return []
        orm_students = self._session.scalars(
            select(StudentORM).where(StudentORM.id.in_(student_ids))
        ).all()
        return [student_from_orm(s) for s in orm_students]


class SqlStudentAnswerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, answer: StudentAnswer) -> None:
        existing = self._session.get(StudentAnswerORM, answer.id)
        if existing:
            existing.answer_content = answer.answer_content.model_dump(exclude_none=True)
            existing.source = answer.source.value
            existing.extraction_confidence = answer.extraction_confidence
        else:
            self._session.add(student_answer_to_orm(answer))
        self._session.commit()

    def get_by_student_and_exam(
        self, student_id: str, exam_id: str
    ) -> list[StudentAnswer]:
        orm_answers = self._session.scalars(
            select(StudentAnswerORM).where(
                StudentAnswerORM.student_id == student_id,
                StudentAnswerORM.exam_id == exam_id,
            )
        ).all()
        return [student_answer_from_orm(a) for a in orm_answers]

    def get_by_exam(self, exam_id: str) -> list[StudentAnswer]:
        orm_answers = self._session.scalars(
            select(StudentAnswerORM).where(StudentAnswerORM.exam_id == exam_id)
        ).all()
        return [student_answer_from_orm(a) for a in orm_answers]
