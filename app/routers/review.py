# * ==============================================================================
# *                          Router: Review Queue
# * ==============================================================================
# ? این همان چیزی است که در فاز ۴ عمداً به تعویق افتاد: حالا که GradeResult
# ? واقعاً ذخیره می‌شود، ReviewQueue می‌تواند از طریق API استفاده شود.

from fastapi import APIRouter, HTTPException

from app.dependencies import (
    ExamRepositoryDep,
    GradeResultRepositoryDep,
    StudentRepositoryDep,
)
from app.schemas import ReviewQueueItemResponse, TeacherOverrideRequest
from confidence.review_queue import InvalidOverrideScoreError, ReviewQueue
from domain.models.grading_result import GradeResult

router = APIRouter(prefix="/review-queue", tags=["review"])


@router.get("", response_model=list[ReviewQueueItemResponse])
def list_review_queue(
    grade_result_repository: GradeResultRepositoryDep,
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    exam_id: str | None = None,
) -> list[ReviewQueueItemResponse]:
    # ? اگر exam_id داده شود، فقط همان آزمون فیلتر می‌شود؛ وگرنه صف بازبینی
    # ? سراسری (همه آزمون‌ها) برمی‌گردد - همان‌طور که در طراحی اولیه پنل خواسته شد.
    all_results = (
        grade_result_repository.get_by_exam(exam_id)
        if exam_id
        else grade_result_repository.list_all()
    )
    needing_review = ReviewQueue.filter_needing_review(all_results)
    if not needing_review:
        return []

    # ! واکشی دسته‌ای: به‌جای یک Query به‌ازای هر آیتم صف (N+1)، فقط سه Query
    # ! کلی - یکی برای همه دانش‌آموزان درگیر، یکی برای همه آزمون‌ها، یکی برای
    # ! همه سؤالات - صرف‌نظر از این‌که صف چند ردیف دارد.
    student_ids = list({result.student_id for result in needing_review})
    exam_ids = list({result.exam_id for result in needing_review})
    question_ids = list({result.question_id for result in needing_review})

    students_by_id = {s.id: s for s in student_repository.get_many_by_ids(student_ids)}
    exams_by_id = {e.id: e for e in exam_repository.get_many_by_ids(exam_ids)}
    questions_by_id = {
        q.id: q for q in exam_repository.get_questions_by_ids(question_ids)
    }

    items = []
    for result in needing_review:
        student = students_by_id.get(result.student_id)
        exam = exams_by_id.get(result.exam_id)
        question = questions_by_id.get(result.question_id)
        items.append(
            ReviewQueueItemResponse(
                grade_result=result,
                # ! این مقادیر پیش‌فرض ("نامشخص") فقط برای ناسازگاری داده غیرمنتظره
                # ! هستند (مثلاً رکورد یتیم) - در جریان عادی همیشه پیدا می‌شوند
                # ! چون Foreign Key ها این ارتباط را تضمین می‌کنند.
                student_full_name=student.full_name if student else "نامشخص",
                student_code=student.student_code if student else None,
                exam_title=exam.title if exam else "نامشخص",
                question_text=question.question_text if question else "نامشخص",
                question_topic=question.topic if question else None,
            )
        )
    return items


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
