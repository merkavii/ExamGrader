# * ==============================================================================
# *                    StudentRepository (Interface)
# * ==============================================================================

from typing import Protocol

from domain.models.student import Student, StudentAnswer


class StudentRepository(Protocol):
    def save(self, student: Student) -> None: ...

    def get_by_id(self, student_id: str) -> Student | None: ...

    def list_by_exam(self, exam_id: str) -> list[Student]: ...


class StudentAnswerRepository(Protocol):
    def save(self, answer: StudentAnswer) -> None: ...

    def get_by_student_and_exam(
        self, student_id: str, exam_id: str
    ) -> list[StudentAnswer]: ...

    def get_by_exam(self, exam_id: str) -> list[StudentAnswer]: ...
