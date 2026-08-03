# * ==============================================================================
# *                  SqlSchoolClassRepository (Implementation)
# * ==============================================================================

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models.school_class import SchoolClass
from infrastructure.database.mappers import school_class_from_orm, school_class_to_orm
from infrastructure.database.models import SchoolClassORM


class SqlSchoolClassRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, school_class: SchoolClass) -> None:
        existing = self._session.get(SchoolClassORM, school_class.id)
        if existing:
            existing.name = school_class.name
            existing.academic_year = school_class.academic_year
        else:
            self._session.add(school_class_to_orm(school_class))
        self._session.commit()

    def get_by_id(self, class_id: str) -> SchoolClass | None:
        orm_class = self._session.get(SchoolClassORM, class_id)
        return school_class_from_orm(orm_class) if orm_class else None

    def list_all(self) -> list[SchoolClass]:
        orm_classes = self._session.scalars(select(SchoolClassORM)).all()
        return [school_class_from_orm(c) for c in orm_classes]
