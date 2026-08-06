# * ==============================================================================
# *                          Router: Classes
# * ==============================================================================

from fastapi import APIRouter, HTTPException

from app.dependencies import SchoolClassRepositoryDep, StudentRepositoryDep
from app.schemas import SchoolClassCreateRequest
from domain.models.school_class import SchoolClass
from domain.models.student import Student

router = APIRouter(prefix="/classes", tags=["classes"])


@router.post("", response_model=SchoolClass, status_code=201)
def create_class(
    request: SchoolClassCreateRequest, class_repository: SchoolClassRepositoryDep
) -> SchoolClass:
    school_class = SchoolClass(name=request.name, academic_year=request.academic_year)
    class_repository.save(school_class)
    return school_class


@router.get("", response_model=list[SchoolClass])
def list_classes(class_repository: SchoolClassRepositoryDep) -> list[SchoolClass]:
    return class_repository.list_all()


@router.get("/{class_id}", response_model=SchoolClass)
def get_class(class_id: str, class_repository: SchoolClassRepositoryDep) -> SchoolClass:
    school_class = class_repository.get_by_id(class_id)
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    return school_class


@router.get("/{class_id}/students", response_model=list[Student])
def list_students_in_class(
    class_id: str,
    class_repository: SchoolClassRepositoryDep,
    student_repository: StudentRepositoryDep,
) -> list[Student]:
    if not class_repository.get_by_id(class_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return student_repository.list_by_class(class_id)
