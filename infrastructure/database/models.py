# * ==============================================================================
# *                        SQLAlchemy ORM Models
# * ==============================================================================
# ! این فایل تنها جایی است که ساختار جدول‌های دیتابیس تعریف می‌شود.
# ! Domain Layer هیچ‌وقت نباید این فایل را import کند - فقط infrastructure/repositories
# ! اجازه دارد بین این مدل‌ها و مدل‌های Pydantic در domain/models تبدیل انجام دهد.
# ? فیلدهایی مثل correct_answer که در Pydantic ساختار تو در تو دارند، اینجا به‌صورت
# ? JSON ذخیره می‌شوند - SQLAlchemy روی SQLite این را به‌صورت TEXT سریالایز می‌کند.

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExamORM(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)

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

    exam: Mapped["ExamORM"] = relationship(back_populates="questions")


class StudentORM(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)


class StudentAnswerORM(Base):
    __tablename__ = "student_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    exam_id: Mapped[str] = mapped_column(ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    extraction_confidence: Mapped[float | None] = mapped_column(nullable=True)
