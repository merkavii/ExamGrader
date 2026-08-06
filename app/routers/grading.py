# * ==============================================================================
# *                          Router: Grading
# * ==============================================================================
# ? دقیقاً همان چیزی که از ابتدای پروژه خواسته شد: معلم می‌تواند یا کل کلاس
# ? را یک‌جا تصحیح کند («Grade All»)، یا فقط یک برگه مشخص را («Grade This Sheet»).
# ? هر دو از یک GradingService.grade_student مشترک استفاده می‌کنند - تفاوت فقط
# ? در دامنه (scope) است، نه در منطق تصحیح.

from fastapi import APIRouter, HTTPException

from app.dependencies import (
    ExamRepositoryDep,
    GradeResultRepositoryDep,
    GradingServiceDep,
    StudentRepositoryDep,
)
from domain.models.grading_result import GradeResult
from grading.aggregator import ExamScoreSummary
from grading.grading_service import ExamNotFoundError, StudentNotFoundError

router = APIRouter(prefix="/exams/{exam_id}", tags=["grading"])


@router.post("/students/{student_id}/grade", response_model=list[GradeResult])
def grade_single_sheet(
    exam_id: str, student_id: str, grading_service: GradingServiceDep
) -> list[GradeResult]:
    try:
        return grading_service.grade_student(exam_id, student_id)
    except ExamNotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except StudentNotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")


@router.get("/students/{student_id}/results", response_model=list[GradeResult])
def get_student_results(
    exam_id: str,
    student_id: str,
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    grade_result_repository: GradeResultRepositoryDep,
) -> list[GradeResult]:
    # ? برخلاف POST .../grade (که همیشه دوباره تصحیح می‌کند)، این endpoint فقط
    # ? می‌خواند - نه محاسبه‌ای دارد، نه (برای سؤالات LLM-based) تماسی با Ollama.
    # ? برای صفحه «نمایش نمره و جزئیات تصحیح» دقیقاً همین لازم است.
    if not exam_repository.get_by_id(exam_id):
        raise HTTPException(status_code=404, detail="Exam not found")
    if not student_repository.get_by_id(student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    return grade_result_repository.get_by_student_and_exam(student_id, exam_id)


@router.post("/grade", response_model=dict[str, list[GradeResult]])
def grade_all_sheets(
    exam_id: str, grading_service: GradingServiceDep
) -> dict[str, list[GradeResult]]:
    try:
        return grading_service.grade_exam(exam_id)
    except ExamNotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")


@router.get("/results", response_model=list[ExamScoreSummary])
def get_exam_results(
    exam_id: str, grading_service: GradingServiceDep
) -> list[ExamScoreSummary]:
    # ? نتایج «پایه» - از GradeResult های از قبل ذخیره‌شده، بدون تصحیح مجدد.
    # ? اگر معلم هنوز روی «Grade All» یا «Grade This Sheet» نزده، لیست خالی
    # ? برمی‌گردد - نه خطا.
    try:
        return grading_service.get_exam_results(exam_id)
    except ExamNotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
