# * ==============================================================================
# *                          Router: Students
# * ==============================================================================

from fastapi import APIRouter, HTTPException

from app.dependencies import SchoolClassRepositoryDep, StudentRepositoryDep
from app.schemas import StudentCreateRequest
from domain.models.student import Student

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=Student, status_code=201)
def create_student(
    request: StudentCreateRequest,
    student_repository: StudentRepositoryDep,
    class_repository: SchoolClassRepositoryDep,
) -> Student:
    # ! اگر class_id داده شده، باید واقعاً وجود داشته باشد - وگرنه دانش‌آموز به
    # ! یک کلاس ناموجود اشاره می‌کند و list_by_class بعداً نتیجه گمراه‌کننده می‌دهد.
    if request.class_id and not class_repository.get_by_id(request.class_id):
        raise HTTPException(status_code=404, detail="Class not found")

    student = Student(
        full_name=request.full_name,
        student_code=request.student_code,
        class_id=request.class_id,
    )
    student_repository.save(student)
    return student


@router.get("", response_model=list[Student])
def list_students(student_repository: StudentRepositoryDep) -> list[Student]:
    return student_repository.list_all()
