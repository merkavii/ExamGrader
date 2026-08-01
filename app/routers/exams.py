# * ==============================================================================
# *                          Router: Exams / Questions
# * ==============================================================================

from fastapi import APIRouter, HTTPException

from app.dependencies import ExamRepositoryDep
from app.schemas import ExamCreateRequest, QuestionCreateRequest
from domain.models.exam import Exam, Question
from input.manual.manual_input_handler import build_question_from_manual_input

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("", response_model=Exam, status_code=201)
def create_exam(request: ExamCreateRequest, exam_repository: ExamRepositoryDep) -> Exam:
    exam = Exam(title=request.title)
    exam_repository.save(exam)
    return exam


@router.get("", response_model=list[Exam])
def list_exams(exam_repository: ExamRepositoryDep) -> list[Exam]:
    return exam_repository.list_all()


@router.get("/{exam_id}", response_model=Exam)
def get_exam(exam_id: str, exam_repository: ExamRepositoryDep) -> Exam:
    exam = exam_repository.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.post("/{exam_id}/questions", response_model=Question, status_code=201)
def add_question(
    exam_id: str,
    request: QuestionCreateRequest,
    exam_repository: ExamRepositoryDep,
) -> Question:
    exam = exam_repository.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # ! اعتبارسنجی کامل سؤال (مثلاً تطبیق rubric با max_score) همین‌جا از طریق
    # ! سازنده Question اتفاق می‌افتد و اگر نامعتبر باشد، pydantic ValidationError
    # ! می‌دهد که FastAPI آن را به‌صورت خودکار به پاسخ 422 تبدیل می‌کند.
    question = build_question_from_manual_input(
        exam_id=exam_id,
        question_text=request.question_text,
        question_type=request.question_type,
        correct_answer=request.correct_answer,
        max_score=request.max_score,
        numeric_tolerance=request.numeric_tolerance,
        rubric=request.rubric,
        options=request.options,
    )
    exam_repository.add_question(question)
    return question


@router.get("/{exam_id}/questions", response_model=list[Question])
def list_questions(exam_id: str, exam_repository: ExamRepositoryDep) -> list[Question]:
    exam = exam_repository.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam_repository.list_questions(exam_id)
