# * ==============================================================================
# *                              Dependencies
# * ==============================================================================
# ? این فایل نقطه‌ای است که FastAPI را به infrastructure وصل می‌کند.
# ! روترها (app/routers/*.py) نباید مستقیماً SqlExamRepository را import کنند؛
# ! باید فقط این Depends ها را بگیرند - این‌طوری اگر فردا خواستیم Repository
# ! را عوض کنیم (مثلاً برای تست با In-Memory Repository)، فقط همین فایل عوض می‌شود.

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database.session import get_db_session
from infrastructure.repositories.sql_exam_repository import SqlExamRepository
from infrastructure.repositories.sql_grade_result_repository import (
    SqlGradeResultRepository,
)
from infrastructure.repositories.sql_school_class_repository import (
    SqlSchoolClassRepository,
)
from infrastructure.repositories.sql_student_repository import (
    SqlStudentAnswerRepository,
    SqlStudentRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_exam_repository(session: DbSession) -> SqlExamRepository:
    return SqlExamRepository(session)


def get_student_repository(session: DbSession) -> SqlStudentRepository:
    return SqlStudentRepository(session)


def get_student_answer_repository(session: DbSession) -> SqlStudentAnswerRepository:
    return SqlStudentAnswerRepository(session)


def get_grade_result_repository(session: DbSession) -> SqlGradeResultRepository:
    return SqlGradeResultRepository(session)


def get_school_class_repository(session: DbSession) -> SqlSchoolClassRepository:
    return SqlSchoolClassRepository(session)


ExamRepositoryDep = Annotated[SqlExamRepository, Depends(get_exam_repository)]
StudentRepositoryDep = Annotated[SqlStudentRepository, Depends(get_student_repository)]
StudentAnswerRepositoryDep = Annotated[
    SqlStudentAnswerRepository, Depends(get_student_answer_repository)
]
GradeResultRepositoryDep = Annotated[
    SqlGradeResultRepository, Depends(get_grade_result_repository)
]
SchoolClassRepositoryDep = Annotated[
    SqlSchoolClassRepository, Depends(get_school_class_repository)
]
