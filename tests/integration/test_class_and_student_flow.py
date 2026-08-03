# * ==============================================================================
# *              Integration Test: Class + Student Flow
# * ==============================================================================
# ? هدف: تضمین این‌که «کلاس یا گروه آموزشی» - یکی از موارد صریح خواسته‌شده در
# ? بررسی معماری - واقعاً از طریق API کار می‌کند: ساخت کلاس، عضویت دانش‌آموز،
# ? و بازیابی لیست دانش‌آموزان یک کلاس.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_db_session
from app.main import app
from infrastructure.database.models import Base


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_class_assign_student_and_list_class_members(client: TestClient):
    # * ۱. ساخت کلاس
    class_response = client.post(
        "/classes", json={"name": "هفتم الف", "academic_year": "1404-1405"}
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    # * ۲. ساخت دانش‌آموز با عضویت در همین کلاس + کد دانش‌آموزی
    student_response = client.post(
        "/students",
        json={"full_name": "سارا محمدی", "student_code": "S-1023", "class_id": class_id},
    )
    assert student_response.status_code == 201
    assert student_response.json()["student_code"] == "S-1023"

    # * ۳. بازخوانی لیست دانش‌آموزان این کلاس
    members = client.get(f"/classes/{class_id}/students")
    assert members.status_code == 200
    assert len(members.json()) == 1
    assert members.json()[0]["full_name"] == "سارا محمدی"


def test_create_student_with_nonexistent_class_is_rejected(client: TestClient):
    # ! نباید بشود دانش‌آموزی به کلاس ناموجود اشاره کند
    response = client.post(
        "/students", json={"full_name": "علی رضایی", "class_id": "class-does-not-exist"}
    )
    assert response.status_code == 404


def test_list_classes_returns_created_class(client: TestClient):
    client.post("/classes", json={"name": "هشتم ب"})
    classes = client.get("/classes")
    assert classes.status_code == 200
    assert any(c["name"] == "هشتم ب" for c in classes.json())
