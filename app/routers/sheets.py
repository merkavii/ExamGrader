# * ==============================================================================
# *                          Router: Sheets
# * ==============================================================================
# ? "Sheet" یک مفهوم View-level است: مجموعه پاسخ‌های یک دانش‌آموز مشخص برای
# ? یک آزمون مشخص. این یک Entity مستقل در Domain نیست - فقط ترکیبی از
# ? StudentAnswer های موجود برای نمایش راحت‌تر در پنل معلم.

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.dependencies import (
    AnswerSheetExtractorDep,
    ExamRepositoryDep,
    StudentAnswerRepositoryDep,
    StudentRepositoryDep,
)
from app.schemas import SheetStatusResponse, SheetSubmitRequest
from domain.models.student import StudentAnswer
from extraction.answer_sheet_extractor import AnswerSheetExtractionResult
from input.manual.manual_input_handler import build_student_answer_from_manual_input

router = APIRouter(prefix="/exams/{exam_id}/students/{student_id}/answers", tags=["sheets"])


@router.post("", response_model=list[StudentAnswer], status_code=201)
def submit_sheet(
    exam_id: str,
    student_id: str,
    request: SheetSubmitRequest,
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    student_answer_repository: StudentAnswerRepositoryDep,
) -> list[StudentAnswer]:
    if not exam_repository.get_by_id(exam_id):
        raise HTTPException(status_code=404, detail="Exam not found")
    if not student_repository.get_by_id(student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    valid_question_ids = {q.id for q in exam_repository.list_questions(exam_id)}

    saved_answers: list[StudentAnswer] = []
    for item in request.answers:
        # ! پاسخ به سؤالی که به این آزمون تعلق ندارد نباید ثبت شود -
        # ! این یک اعتبارسنجی سطح API است، نه سطح مدل Domain، چون به
        # ! context (exam_id) نیاز دارد که StudentAnswer به‌تنهایی آن را ندارد.
        if item.question_id not in valid_question_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Question {item.question_id} does not belong to exam {exam_id}",
            )

        answer = build_student_answer_from_manual_input(
            exam_id=exam_id,
            student_id=student_id,
            question_id=item.question_id,
            answer_content=item.answer_content,
            source=request.source,
        )
        student_answer_repository.save(answer)
        saved_answers.append(answer)

    return saved_answers


@router.post("/extract-from-image", response_model=AnswerSheetExtractionResult)
async def extract_answers_from_image(
    exam_id: str,
    student_id: str,
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    extractor: AnswerSheetExtractorDep,
    image: UploadFile = File(...),
) -> AnswerSheetExtractionResult:
    """
    ? یک عکس از برگه پاسخ دانش‌آموز می‌گیرد و پیشنهاد پاسخ هر سؤال را برمی‌گرداند.

    ! این endpoint هیچ‌چیز در دیتابیس ذخیره نمی‌کند - فقط "پیشنهاد" است. ثبت
    ! نهایی همچنان از طریق POST .../answers (همین روتر، بالاتر) با
    ! source="image" انجام می‌شود؛ معلم باید قبل از آن نتیجه را در Frontend
    ! ببیند و در صورت نیاز اصلاح کند - طبق قانون همیشگی این پروژه.
    """
    if not exam_repository.get_by_id(exam_id):
        raise HTTPException(status_code=404, detail="Exam not found")
    if not student_repository.get_by_id(student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    questions = exam_repository.list_questions(exam_id)
    if not questions:
        raise HTTPException(
            status_code=400, detail="Exam has no questions to extract answers for"
        )

    image_bytes = await image.read()
    return extractor.extract(image_bytes, questions)


@router.get("", response_model=list[StudentAnswer])
def get_sheet(
    exam_id: str,
    student_id: str,
    student_answer_repository: StudentAnswerRepositoryDep,
) -> list[StudentAnswer]:
    return student_answer_repository.get_by_student_and_exam(student_id, exam_id)


sheet_status_router = APIRouter(prefix="/exams/{exam_id}/sheets", tags=["sheets"])


@sheet_status_router.get("", response_model=list[SheetStatusResponse])
def list_sheet_statuses(
    exam_id: str,
    exam_repository: ExamRepositoryDep,
    student_repository: StudentRepositoryDep,
    student_answer_repository: StudentAnswerRepositoryDep,
) -> list[SheetStatusResponse]:
    # ? این endpoint دقیقاً همان چیزی است که تب "Sheets" در پنل معلم نمایش می‌دهد:
    # ? لیست دانش‌آموزانی که برای این آزمون پاسخ ثبت کرده‌اند + میزان پیشرفت.
    if not exam_repository.get_by_id(exam_id):
        raise HTTPException(status_code=404, detail="Exam not found")

    total_questions = len(exam_repository.list_questions(exam_id))
    all_answers = student_answer_repository.get_by_exam(exam_id)

    answered_by_student: dict[str, set[str]] = {}
    for answer in all_answers:
        answered_by_student.setdefault(answer.student_id, set()).add(answer.question_id)

    statuses = []
    for student_id, question_ids in answered_by_student.items():
        student = student_repository.get_by_id(student_id)
        if not student:
            continue  # ! داده ناسازگار - نباید رخ دهد، ولی صامت رد نمی‌کنیم بدون بررسی
        statuses.append(
            SheetStatusResponse(
                student_id=student.id,
                student_full_name=student.full_name,
                answered_questions=len(question_ids),
                total_questions=total_questions,
            )
        )
    return statuses
