# * ==============================================================================
# *              Integration Test: Analytics API (Full HTTP Flow)
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


def test_class_and_student_analytics_after_grading_two_students(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون فیزیک"}).json()["id"]

    question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "آب در صفر درجه یخ می‌زند؟",
            "question_type": "true_false",
            "correct_answer": {"selected_option": "true"},
            "max_score": 1,
            "topic": "فیزیک",
        },
    ).json()

    # ? دانش‌آموز اول درست پاسخ می‌دهد، دومی غلط - برای تولید پراکندگی واقعی
    student_a = client.post("/students", json={"full_name": "سارا محمدی"}).json()
    student_b = client.post("/students", json={"full_name": "علی رضایی"}).json()

    client.post(
        f"/exams/{exam_id}/students/{student_a['id']}/answers",
        json={"answers": [{"question_id": question["id"], "answer_content": {"selected_option": "true"}}]},
    )
    client.post(
        f"/exams/{exam_id}/students/{student_b['id']}/answers",
        json={"answers": [{"question_id": question["id"], "answer_content": {"selected_option": "false"}}]},
    )

    client.post(f"/exams/{exam_id}/grade")

    # * آمار سطح کلاس
    class_analytics = client.get(f"/exams/{exam_id}/analytics").json()
    assert class_analytics["participant_count"] == 2
    assert class_analytics["average_percentage"] == 50.0
    assert class_analytics["topic_breakdown"]["فیزیک"] == 50.0

    # * تحلیل دانش‌آموز اول (نمره کامل)
    student_analytics = client.get(f"/students/{student_a['id']}/analytics").json()
    assert student_analytics["overall_average_percentage"] == 100.0
    assert student_analytics["exam_history"][0]["exam_id"] == exam_id

    # * مقایسه دانش‌آموز اول با میانگین کلاس (باید بالاتر باشد)
    comparison = client.get(f"/students/{student_a['id']}/analytics/compare/{exam_id}").json()
    assert comparison["student_percentage"] == 100.0
    assert comparison["difference"] == 50.0


def test_exam_analytics_before_grading_returns_empty_not_error(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون تصحیح‌نشده"}).json()["id"]

    response = client.get(f"/exams/{exam_id}/analytics")
    assert response.status_code == 200
    assert response.json()["participant_count"] == 0


def test_compare_returns_404_when_exam_has_no_graded_results(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون تصحیح‌نشده"}).json()["id"]
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]

    response = client.get(f"/students/{student_id}/analytics/compare/{exam_id}")
    assert response.status_code == 404
