# * ==============================================================================
# *                          Router: Review Queue
# * ==============================================================================
# ? این همان چیزی است که در فاز ۴ عمداً به تعویق افتاد: حالا که GradeResult
# ? واقعاً ذخیره می‌شود، ReviewQueue می‌تواند از طریق API استفاده شود.

from fastapi import APIRouter, HTTPException

from app.dependencies import GradeResultRepositoryDep
from app.schemas import TeacherOverrideRequest
from confidence.review_queue import InvalidOverrideScoreError, ReviewQueue
from domain.models.grading_result import GradeResult

router = APIRouter(prefix="/review-queue", tags=["review"])


@router.get("", response_model=list[GradeResult])
def list_review_queue(
    grade_result_repository: GradeResultRepositoryDep,
    exam_id: str | None = None,
) -> list[GradeResult]:
    # ? اگر exam_id داده شود، فقط همان آزمون فیلتر می‌شود؛ وگرنه صف بازبینی
    # ? سراسری (همه آزمون‌ها) برمی‌گردد - همان‌طور که در طراحی اولیه پنل خواسته شد.
    all_results = (
        grade_result_repository.get_by_exam(exam_id)
        if exam_id
        else grade_result_repository.list_all()
    )
    return ReviewQueue.filter_needing_review(all_results)


@router.post("/{grade_result_id}/override", response_model=GradeResult)
def override_grade_result(
    grade_result_id: str,
    request: TeacherOverrideRequest,
    grade_result_repository: GradeResultRepositoryDep,
) -> GradeResult:
    existing = grade_result_repository.get_by_id(grade_result_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Grade result not found")

    try:
        overridden = ReviewQueue.apply_teacher_override(
            existing,
            final_score=request.final_score,
            teacher_reasoning=request.teacher_reasoning,
        )
    except InvalidOverrideScoreError as error:
        raise HTTPException(status_code=422, detail=str(error))

    grade_result_repository.save(overridden)
    return overridden
