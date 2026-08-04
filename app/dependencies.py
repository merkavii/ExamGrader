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

from ai.ollama_provider import OllamaProvider
from analytics.class_analytics import ClassAnalyticsService
from analytics.student_analytics import StudentAnalyticsService
from config.settings import get_settings
from grading.grading_service import GradingService
from grading.orchestrator import GradingOrchestrator
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


def get_llm_client() -> OllamaProvider:
    # ? هر Request یک instance جدید می‌گیرد - سبک است (فقط نگه‌دارنده تنظیمات)،
    # ! نیازی به cache کردن نیست. آدرس/مدل از config/settings.py می‌آید تا بدون
    # ! تغییر کد قابل تنظیم باشد.
    settings = get_settings()
    return OllamaProvider(model=settings.ollama_model, base_url=settings.ollama_base_url)


def get_grading_orchestrator(
    llm_client: Annotated[OllamaProvider, Depends(get_llm_client)],
) -> GradingOrchestrator:
    return GradingOrchestrator(llm_client=llm_client)


def get_grading_service(
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    student_answer_repository: StudentAnswerRepositoryDep,
    grade_result_repository: GradeResultRepositoryDep,
    orchestrator: Annotated[GradingOrchestrator, Depends(get_grading_orchestrator)],
) -> GradingService:
    return GradingService(
        exam_repository=exam_repository,
        student_repository=student_repository,
        student_answer_repository=student_answer_repository,
        grade_result_repository=grade_result_repository,
        orchestrator=orchestrator,
    )


GradingServiceDep = Annotated[GradingService, Depends(get_grading_service)]


def get_class_analytics_service(
    exam_repository: ExamRepositoryDep,
    grade_result_repository: GradeResultRepositoryDep,
) -> ClassAnalyticsService:
    return ClassAnalyticsService(
        exam_repository=exam_repository, grade_result_repository=grade_result_repository
    )


def get_student_analytics_service(
    exam_repository: ExamRepositoryDep,
    grade_result_repository: GradeResultRepositoryDep,
) -> StudentAnalyticsService:
    return StudentAnalyticsService(
        exam_repository=exam_repository, grade_result_repository=grade_result_repository
    )


ClassAnalyticsServiceDep = Annotated[
    ClassAnalyticsService, Depends(get_class_analytics_service)
]
StudentAnalyticsServiceDep = Annotated[
    StudentAnalyticsService, Depends(get_student_analytics_service)
]
