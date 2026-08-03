# * ==============================================================================
# *                        SQLAlchemy ORM Models
# * ==============================================================================
# ! این فایل تنها جایی است که ساختار جدول‌های دیتابیس تعریف می‌شود.
# ! Domain Layer هیچ‌وقت نباید این فایل را import کند - فقط infrastructure/repositories
# ! اجازه دارد بین این مدل‌ها و مدل‌های Pydantic در domain/models تبدیل انجام دهد.
# ? فیلدهایی مثل correct_answer که در Pydantic ساختار تو در تو دارند، اینجا به‌صورت
# ? JSON ذخیره می‌شوند - SQLAlchemy روی SQLite این را به‌صورت TEXT سریالایز می‌کند.

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExamORM(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    questions: Mapped[list["QuestionORM"]] = relationship(
        back_populates="exam", cascade="all, delete-orphan"
    )


class QuestionORM(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    exam_id: Mapped[str] = mapped_column(ForeignKey("exams.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[dict] = mapped_column(JSON, nullable=False)
    max_score: Mapped[float] = mapped_column(nullable=False)
    numeric_tolerance: Mapped[float | None] = mapped_column(nullable=True)
    rubric: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    topic: Mapped[str | None] = mapped_column(String, nullable=True)

    exam: Mapped["ExamORM"] = relationship(back_populates="questions")


class SchoolClassORM(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String, nullable=True)


class StudentORM(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    student_code: Mapped[str | None] = mapped_column(String, nullable=True)
    class_id: Mapped[str | None] = mapped_column(ForeignKey("classes.id"), nullable=True)


class StudentAnswerORM(Base):
    __tablename__ = "student_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    exam_id: Mapped[str] = mapped_column(ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    extraction_confidence: Mapped[float | None] = mapped_column(nullable=True)


class GradeResultORM(Base):
    __tablename__ = "grade_results"
    __table_args__ = (
        # ! این constraint دقیقاً همان چیزی است که idempotency تصحیح مجدد را
        # ! در سطح دیتابیس تضمین می‌کند - حتی اگر کد Repository اشتباه کند،
        # ! دیتابیس اجازه دو ردیف برای یک (exam, student, question) را نمی‌دهد.
        UniqueConstraint(
            "exam_id", "student_id", "question_id", name="uq_grade_result_triple"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    exam_id: Mapped[str] = mapped_column(ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    max_score: Mapped[float] = mapped_column(nullable=False)
    reasoning: Mapped[str] = mapped_column(String, nullable=False)
    # ? ConfidenceScore کامل به‌صورت JSON ذخیره می‌شود - مثل الگوی correct_answer
    # ? در QuestionORM - چون یک شیء تو در تو با فیلدهای ثابت و کوچک است.
    confidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    grading_method: Mapped[str] = mapped_column(String, nullable=False)
    graded_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
