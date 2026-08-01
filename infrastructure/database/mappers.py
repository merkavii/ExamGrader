# * ==============================================================================
# *                       ORM <-> Domain Mappers
# * ==============================================================================
# ? این فایل تنها نقطه‌ای است که مدل‌های ORM (infrastructure) و مدل‌های Domain
# ? (Pydantic) به هم تبدیل می‌شوند. هیچ کد دیگری در پروژه نباید مستقیماً
# ? ORM را به Domain (یا برعکس) تبدیل کند - این جلوی پخش‌شدن این منطق در کل
# ? پروژه را می‌گیرد و اگر ساختار ORM عوض شود، فقط همین فایل تغییر می‌کند.

from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.rubric import Rubric
from domain.models.student import AnswerContent, Student, StudentAnswer
from infrastructure.database.models import (
    ExamORM,
    QuestionORM,
    StudentAnswerORM,
    StudentORM,
)


def question_to_orm(question: Question) -> QuestionORM:
    return QuestionORM(
        id=question.id,
        exam_id=question.exam_id,
        question_text=question.question_text,
        question_type=question.question_type.value,
        correct_answer=question.correct_answer.model_dump(exclude_none=True),
        max_score=question.max_score,
        numeric_tolerance=question.numeric_tolerance,
        rubric=question.rubric.model_dump() if question.rubric else None,
        options=question.options,
    )


def question_from_orm(orm_question: QuestionORM) -> Question:
    return Question(
        id=orm_question.id,
        exam_id=orm_question.exam_id,
        question_text=orm_question.question_text,
        question_type=orm_question.question_type,
        correct_answer=CorrectAnswer(**orm_question.correct_answer),
        max_score=orm_question.max_score,
        numeric_tolerance=orm_question.numeric_tolerance,
        rubric=Rubric(**orm_question.rubric) if orm_question.rubric else None,
        options=orm_question.options,
    )


def exam_to_orm(exam: Exam) -> ExamORM:
    return ExamORM(
        id=exam.id,
        title=exam.title,
        questions=[question_to_orm(question) for question in exam.questions],
    )


def exam_from_orm(orm_exam: ExamORM) -> Exam:
    return Exam(
        id=orm_exam.id,
        title=orm_exam.title,
        questions=[question_from_orm(q) for q in orm_exam.questions],
    )


def student_to_orm(student: Student) -> StudentORM:
    return StudentORM(id=student.id, full_name=student.full_name)


def student_from_orm(orm_student: StudentORM) -> Student:
    return Student(id=orm_student.id, full_name=orm_student.full_name)


def student_answer_to_orm(answer: StudentAnswer) -> StudentAnswerORM:
    return StudentAnswerORM(
        id=answer.id,
        exam_id=answer.exam_id,
        student_id=answer.student_id,
        question_id=answer.question_id,
        answer_content=answer.answer_content.model_dump(exclude_none=True),
        source=answer.source.value,
        extraction_confidence=answer.extraction_confidence,
    )


def student_answer_from_orm(orm_answer: StudentAnswerORM) -> StudentAnswer:
    return StudentAnswer(
        id=orm_answer.id,
        exam_id=orm_answer.exam_id,
        student_id=orm_answer.student_id,
        question_id=orm_answer.question_id,
        answer_content=AnswerContent(**orm_answer.answer_content),
        source=orm_answer.source,
        extraction_confidence=orm_answer.extraction_confidence,
    )
