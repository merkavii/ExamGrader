# * ==============================================================================
# *                      SqlExamRepository (Implementation)
# * ==============================================================================
# ? پیاده‌سازی واقعی ExamRepository با SQLAlchemy/SQLite.
# ? این کلاس Protocol تعریف‌شده در domain/repositories/exam_repository.py را
# ? بدون وراثت صریح پیاده‌سازی می‌کند (Structural Typing پایتون).

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models.exam import Exam, Question
from infrastructure.database.mappers import (
    exam_from_orm,
    exam_to_orm,
    question_from_orm,
    question_to_orm,
)
from infrastructure.database.models import ExamORM, QuestionORM


class SqlExamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, exam: Exam) -> None:
        existing = self._session.get(ExamORM, exam.id)
        if existing:
            # ! فقط عنوان آزمون آپدیت می‌شود؛ سؤال‌ها از طریق add_question
            # ! مدیریت می‌شوند تا رفتار save غیرقابل‌پیش‌بینی نشود.
            existing.title = exam.title
        else:
            self._session.add(exam_to_orm(exam))
        self._session.commit()

    def get_by_id(self, exam_id: str) -> Exam | None:
        orm_exam = self._session.get(ExamORM, exam_id)
        return exam_from_orm(orm_exam) if orm_exam else None

    def list_all(self) -> list[Exam]:
        orm_exams = self._session.scalars(select(ExamORM)).all()
        return [exam_from_orm(orm_exam) for orm_exam in orm_exams]

    def delete(self, exam_id: str) -> None:
        orm_exam = self._session.get(ExamORM, exam_id)
        if orm_exam:
            self._session.delete(orm_exam)
            self._session.commit()

    def add_question(self, question: Question) -> None:
        self._session.add(question_to_orm(question))
        self._session.commit()

    def get_question(self, question_id: str) -> Question | None:
        orm_question = self._session.get(QuestionORM, question_id)
        return question_from_orm(orm_question) if orm_question else None

    def list_questions(self, exam_id: str) -> list[Question]:
        orm_questions = self._session.scalars(
            select(QuestionORM).where(QuestionORM.exam_id == exam_id)
        ).all()
        return [question_from_orm(q) for q in orm_questions]
