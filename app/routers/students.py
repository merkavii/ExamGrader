# * ==============================================================================
# *                          Router: Students
# * ==============================================================================

from fastapi import APIRouter

from app.dependencies import StudentRepositoryDep
from app.schemas import StudentCreateRequest
from domain.models.student import Student

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=Student, status_code=201)
def create_student(
    request: StudentCreateRequest, student_repository: StudentRepositoryDep
) -> Student:
    student = Student(full_name=request.full_name)
    student_repository.save(student)
    return student


@router.get("", response_model=list[Student])
def list_students(student_repository: StudentRepositoryDep) -> list[Student]:
    return student_repository.list_all()
