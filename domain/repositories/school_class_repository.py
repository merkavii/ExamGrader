# * ==============================================================================
# *                   SchoolClassRepository (Interface)
# * ==============================================================================

from typing import Protocol

from domain.models.school_class import SchoolClass


class SchoolClassRepository(Protocol):
    def save(self, school_class: SchoolClass) -> None: ...

    def get_by_id(self, class_id: str) -> SchoolClass | None: ...

    def list_all(self) -> list[SchoolClass]: ...
