# * ==============================================================================
# *                  Integration Test: GradingService
# * ==============================================================================
# ? هدف این تست دقیقاً معیار موفقیت فاز ۵ است: تصحیح یک آزمون واقعی (شامل هم
# ? سؤال قانون‌محور هم سؤال LLM-based) از ابتدا تا نمره نهایی، به‌علاوه تأیید
# ? این‌که تصحیح مجدد (regrade) رکورد تکراری نمی‌سازد.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domain.models.enums import AnswerSource, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.student import AnswerContent, Student, StudentAnswer
from grading.grading_service import (
    ExamNotFoundError,
    GradingService,
    StudentNotFoundError,
)
from grading.orchestrator import GradingOrchestrator
from infrastructure.database.models import Base
from infrastructure.repositories.sql_exam_repository import SqlExamRepository
from infrastructure.repositories.sql_grade_result_repository import (
    SqlGradeResultRepository,
)
from infrastructure.repositories.sql_student_repository import (
    SqlStudentAnswerRepository,
    SqlStudentRepository,
)
from tests.unit.fakes import FakeLLMClient


@pytest.fixture()
def repos():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    exam_repository = SqlExamRepository(session)
    student_repository = SqlStudentRepository(session)
    student_answer_repository = SqlStudentAnswerRepository(session)
    grade_result_repository = SqlGradeResultRepository(session)

    return exam_repository, student_repository, student_answer_repository, grade_result_repository


def _build_exam_with_two_questions(exam_repository) -> Exam:
    exam = Exam(title="آزمون علوم")
    exam_repository.save(exam)

    mc_question = Question(
        exam_id=exam.id,
        question_text="کدام گزینه سیاره است؟",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer=CorrectAnswer(selected_option="زمین"),
        options=["ماه", "زمین"],
        max_score=1,
    )
    short_answer_question = Question(
        exam_id=exam.id,
        question_text="پایتخت ایران؟",
        question_type=QuestionType.SHORT_ANSWER,
        correct_answer=CorrectAnswer(text="تهران"),
        max_score=1,
    )
    exam_repository.add_question(mc_question)
    exam_repository.add_question(short_answer_question)

    exam.questions = [mc_question, short_answer_question]
    return exam


def _grading_service(repos, fake_llm_response: str) -> GradingService:
    exam_repository, student_repository, student_answer_repository, grade_result_repository = repos
    orchestrator = GradingOrchestrator(
        llm_client=FakeLLMClient(fixed_response=fake_llm_response)
    )
    return GradingService(
        exam_repository=exam_repository,
        student_repository=student_repository,
        student_answer_repository=student_answer_repository,
        grade_result_repository=grade_result_repository,
        orchestrator=orchestrator,
    )


def test_grade_student_handles_rule_based_and_llm_questions(repos):
    exam_repository, student_repository, student_answer_repository, grade_result_repository = repos
    exam = _build_exam_with_two_questions(exam_repository)

    student = Student(full_name="سارا محمدی")
    student_repository.save(student)

    # ? فقط به سؤال چهارگزینه‌ای پاسخ داده - سؤال دوم عمداً بی‌پاسخ می‌ماند
    # ? تا مسیر _build_empty_answer هم تست شود.
    student_answer_repository.save(
        StudentAnswer(
            exam_id=exam.id,
            student_id=student.id,
            question_id=exam.questions[0].id,
            answer_content=AnswerContent(selected_option="زمین"),
            source=AnswerSource.MANUAL,
        )
    )

    service = _grading_service(
        repos, '{"is_correct": true, "reasoning": "پاسخی نبود", "confidence": 90}'
    )
    results = service.grade_student(exam.id, student.id)

    assert len(results) == 2
    mc_result = next(r for r in results if r.question_id == exam.questions[0].id)
    empty_result = next(r for r in results if r.question_id == exam.questions[1].id)

    assert mc_result.score == 1
    assert empty_result.score == 0  # ! پاسخ خالی -> صفر، بدون تماس با LLM

    # ? نتایج واقعاً در دیتابیس ذخیره شده‌اند
    saved = grade_result_repository.get_by_student_and_exam(student.id, exam.id)
    assert len(saved) == 2


def test_regrading_does_not_duplicate_results(repos):
    exam_repository, student_repository, student_answer_repository, grade_result_repository = repos
    exam = _build_exam_with_two_questions(exam_repository)
    student = Student(full_name="علی رضایی")
    student_repository.save(student)

    service = _grading_service(
        repos, '{"is_correct": false, "reasoning": "نادرست", "confidence": 90}'
    )

    service.grade_student(exam.id, student.id)
    service.grade_student(exam.id, student.id)  # ! تصحیح مجدد همان برگه

    saved = grade_result_repository.get_by_student_and_exam(student.id, exam.id)
    assert len(saved) == 2  # نه ۴


def test_grade_exam_grades_all_participating_students(repos):
    exam_repository, student_repository, student_answer_repository, grade_result_repository = repos
    exam = _build_exam_with_two_questions(exam_repository)

    students = [Student(full_name=f"دانش‌آموز {i}") for i in range(3)]
    for student in students:
        student_repository.save(student)
        student_answer_repository.save(
            StudentAnswer(
                exam_id=exam.id,
                student_id=student.id,
                question_id=exam.questions[0].id,
                answer_content=AnswerContent(selected_option="زمین"),
                source=AnswerSource.MANUAL,
            )
        )

    service = _grading_service(
        repos, '{"is_correct": true, "reasoning": "درست", "confidence": 95}'
    )
    results_by_student = service.grade_exam(exam.id)

    assert len(results_by_student) == 3
    for student_id, results in results_by_student.items():
        assert len(results) == 2


def test_get_exam_results_returns_aggregated_summary(repos):
    exam_repository, student_repository, student_answer_repository, grade_result_repository = repos
    exam = _build_exam_with_two_questions(exam_repository)
    student = Student(full_name="سارا محمدی")
    student_repository.save(student)
    student_answer_repository.save(
        StudentAnswer(
            exam_id=exam.id,
            student_id=student.id,
            question_id=exam.questions[0].id,
            answer_content=AnswerContent(selected_option="زمین"),
            source=AnswerSource.MANUAL,
        )
    )

    service = _grading_service(
        repos, '{"is_correct": false, "reasoning": "نادرست", "confidence": 90}'
    )
    service.grade_student(exam.id, student.id)

    summaries = service.get_exam_results(exam.id)
    assert len(summaries) == 1
    assert summaries[0].total_score == 1  # فقط سؤال چهارگزینه‌ای درست بود
    assert summaries[0].max_total_score == 2


def test_grade_student_raises_for_unknown_exam(repos):
    _, student_repository, _, _ = repos
    student = Student(full_name="سارا محمدی")
    student_repository.save(student)

    service = _grading_service(repos, "{}")
    with pytest.raises(ExamNotFoundError):
        service.grade_student("exam-does-not-exist", student.id)


def test_grade_student_raises_for_unknown_student(repos):
    exam_repository, _, _, _ = repos
    exam = _build_exam_with_two_questions(exam_repository)

    service = _grading_service(repos, "{}")
    with pytest.raises(StudentNotFoundError):
        service.grade_student(exam.id, "student-does-not-exist")
