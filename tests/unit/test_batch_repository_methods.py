# * ==============================================================================
# *              Tests: Batch Repository Methods (No N+1)
# * ==============================================================================
# ? هدف: تأیید این‌که get_many_by_ids/get_questions_by_ids واقعاً چند رکورد را
# ? با یک Query برمی‌گردانند - این پایه همان چیزی است که صف بازبینی غنی‌شده
# ? را بدون N+1 ممکن می‌کند.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domain.models.enums import QuestionType
from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.student import Student
from infrastructure.database.models import Base
from infrastructure.repositories.sql_exam_repository import SqlExamRepository
from infrastructure.repositories.sql_student_repository import SqlStudentRepository


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    db_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    yield db_session
    db_session.close()


def test_student_get_many_by_ids_returns_all_matching(session):
    repository = SqlStudentRepository(session)
    students = [Student(full_name=f"دانش‌آموز {i}") for i in range(3)]
    for student in students:
        repository.save(student)

    result = repository.get_many_by_ids([students[0].id, students[2].id])

    assert {s.id for s in result} == {students[0].id, students[2].id}


def test_student_get_many_by_ids_with_empty_list_returns_empty():
    # ? بدون دیتابیس هم باید امن باشد - نباید یک Query با IN() خالی بسازد
    repository = SqlStudentRepository(session=None)
    assert repository.get_many_by_ids([]) == []


def test_exam_get_many_by_ids_returns_all_matching(session):
    repository = SqlExamRepository(session)
    exam1 = Exam(title="آزمون یک")
    exam2 = Exam(title="آزمون دو")
    repository.save(exam1)
    repository.save(exam2)

    result = repository.get_many_by_ids([exam1.id, exam2.id])

    assert {e.title for e in result} == {"آزمون یک", "آزمون دو"}


def test_exam_get_questions_by_ids_returns_all_matching(session):
    repository = SqlExamRepository(session)
    exam = Exam(title="آزمون یک")
    repository.save(exam)

    q1 = Question(
        exam_id=exam.id,
        question_text="سؤال یک",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    q2 = Question(
        exam_id=exam.id,
        question_text="سؤال دو",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    repository.add_question(q1)
    repository.add_question(q2)

    result = repository.get_questions_by_ids([q1.id, q2.id])
    assert {q.question_text for q in result} == {"سؤال یک", "سؤال دو"}
