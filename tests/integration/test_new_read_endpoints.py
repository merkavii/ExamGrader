# * ==============================================================================
# *          Integration Test: New Read-Only Endpoints + CORS
# * ==============================================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_db_session, get_llm_client
from app.main import app
from infrastructure.database.models import Base
from tests.unit.fakes import FakeLLMClient


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
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
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(fixed_response="{}")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_cors_header_present_for_allowed_origin(client: TestClient):
    # ! بدون این هدر، هیچ Frontend جدایی نمی‌تواند به API وصل شود
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "*"


def test_get_student_by_id(client: TestClient):
    student = client.post("/students", json={"full_name": "سارا محمدی"}).json()

    response = client.get(f"/students/{student['id']}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "سارا محمدی"


def test_get_student_by_id_returns_404_for_unknown_id(client: TestClient):
    response = client.get("/students/does-not-exist")
    assert response.status_code == 404


def test_get_class_by_id(client: TestClient):
    school_class = client.post("/classes", json={"name": "هفتم الف"}).json()

    response = client.get(f"/classes/{school_class['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "هفتم الف"


def test_get_class_by_id_returns_404_for_unknown_id(client: TestClient):
    response = client.get("/classes/does-not-exist")
    assert response.status_code == 404


def test_get_student_results_does_not_trigger_regrading(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون"}).json()["id"]
    question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "آب یخ می‌زند؟",
            "question_type": "true_false",
            "correct_answer": {"selected_option": "true"},
            "max_score": 1,
        },
    ).json()
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]
    client.post(
        f"/exams/{exam_id}/students/{student_id}/answers",
        json={"answers": [{"question_id": question["id"], "answer_content": {"selected_option": "true"}}]},
    )

    # ? قبل از هر تصحیحی، نتایج باید خالی باشد - نه این‌که خودش تصحیح کند
    before_grading = client.get(f"/exams/{exam_id}/students/{student_id}/results")
    assert before_grading.status_code == 200
    assert before_grading.json() == []

    client.post(f"/exams/{exam_id}/students/{student_id}/grade")

    after_grading = client.get(f"/exams/{exam_id}/students/{student_id}/results")
    assert len(after_grading.json()) == 1
    assert after_grading.json()[0]["score"] == 1


def test_get_student_results_returns_404_for_unknown_exam_or_student(client: TestClient):
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]
    response = client.get(f"/exams/does-not-exist/students/{student_id}/results")
    assert response.status_code == 404
