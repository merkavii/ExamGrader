# * ==============================================================================
# *              Integration Test: GradeResult Persistence
# * ==============================================================================
# ? هدف: تضمین این‌که GradeResult واقعاً در دیتابیس می‌ماند (نه فقط در حافظه)
# ? و تصحیح مجدد همان (exam, student, question) رکورد تکراری نمی‌سازد.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domain.models.enums import GradingMethod, GradingStatus
from domain.models.grading_result import ConfidenceScore, GradeResult
from infrastructure.database.models import Base
from infrastructure.repositories.sql_grade_result_repository import (
    SqlGradeResultRepository,
)


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db_session = SessionLocal()
    yield db_session
    db_session.close()


def _grade_result(score: float = 1, status: GradingStatus = GradingStatus.GRADED) -> GradeResult:
    return GradeResult(
        exam_id="exam-1",
        student_id="student-1",
        question_id="question-1",
        score=score,
        max_score=2,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=95, final_score=95),
        status=status,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )


def test_grade_result_persists_across_repository_instances(session):
    # ? دو Repository جدا با یک session - شبیه‌سازی دو درخواست HTTP مختلف
    repository_write = SqlGradeResultRepository(session)
    repository_write.save(_grade_result())

    repository_read = SqlGradeResultRepository(session)
    results = repository_read.get_by_exam("exam-1")

    assert len(results) == 1
    assert results[0].score == 1
    assert results[0].grading_method == GradingMethod.RULE_BASED


def test_regrading_same_triple_updates_instead_of_duplicating(session):
    repository = SqlGradeResultRepository(session)

    first_pass = _grade_result(score=1)
    repository.save(first_pass)

    # ! همان (exam_id, student_id, question_id) دوباره ذخیره می‌شود - نباید
    # ! رکورد دوم بسازد، باید همان رکورد را overwrite کند.
    second_pass = _grade_result(score=2)
    repository.save(second_pass)

    results = repository.get_by_exam("exam-1")
    assert len(results) == 1
    assert results[0].score == 2


def test_get_by_student_and_exam_filters_correctly(session):
    repository = SqlGradeResultRepository(session)
    repository.save(_grade_result())

    matching = repository.get_by_student_and_exam("student-1", "exam-1")
    non_matching = repository.get_by_student_and_exam("student-999", "exam-1")

    assert len(matching) == 1
    assert len(non_matching) == 0
