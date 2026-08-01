# * ==============================================================================
# *                          ExamRepository (Interface)
# * ==============================================================================
# ? این فایل فقط یک قرارداد (Protocol) است - هیچ منطق ذخیره‌سازی واقعی اینجا نیست.
# ? پیاده‌سازی واقعی (مثلاً با SQLite) در infrastructure/repositories/ قرار می‌گیرد.
# ! Domain Layer هرگز نباید مستقیماً infrastructure را import کند؛ جهت وابستگی
# ! همیشه از infrastructure به سمت domain است، نه برعکس.

from typing import Protocol

from domain.models.exam import Exam, Question


class ExamRepository(Protocol):
    def save(self, exam: Exam) -> None: ...

    def get_by_id(self, exam_id: str) -> Exam | None: ...

    def list_all(self) -> list[Exam]: ...

    def delete(self, exam_id: str) -> None: ...

    # ? اضافه‌شده در فاز ۱: معلم باید بتواند بعد از ساخت آزمون، سؤال‌ها را
    # ? یکی‌یکی اضافه کند - نیازی به بازنویسی کل Exam نیست.
    def add_question(self, question: Question) -> None: ...

    def get_question(self, question_id: str) -> Question | None: ...

    def list_questions(self, exam_id: str) -> list[Question]: ...
