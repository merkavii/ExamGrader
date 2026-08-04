# * ==============================================================================
# *        Integration Test: Grading + Review API (Full HTTP Flow)
# * ==============================================================================
# ? این تست کل مسیر واقعی معلم را از طریق HTTP شبیه‌سازی می‌کند: ساخت آزمون،
# ? ثبت پاسخ، تصحیح تکی/دسته‌ای، مشاهده نتایج، و بازبینی/Override.
#
# ! get_llm_client هم override می‌شود (نه فقط get_db_session) چون در غیر این
# ! صورت روتر واقعی سعی می‌کند به یک سرور Ollama واقعی وصل شود که در محیط تست
# ! وجود ندارد.

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

    def override_get_llm_client():
        # ? پاسخ ثابت: پاسخ کوتاه همیشه "درست" با confidence پایین تا مسیر
        # ? NEEDS_REVIEW هم در همین تست پوشش داده شود.
        return FakeLLMClient(
            fixed_response='{"is_correct": true, "reasoning": "از نظر معنایی درست است", "confidence": 55}'
        )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_llm_client] = override_get_llm_client
    yield TestClient(app)
    app.dependency_overrides.clear()


def _setup_exam_and_student(client: TestClient) -> dict:
    exam_id = client.post("/exams", json={"title": "آزمون ترکیبی"}).json()["id"]

    mc_question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "کدام گزینه سیاره است؟",
            "question_type": "multiple_choice",
            "correct_answer": {"selected_option": "زمین"},
            "options": ["ماه", "زمین"],
            "max_score": 1,
        },
    ).json()

    short_answer_question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "پایتخت ایران؟",
            "question_type": "short_answer",
            "correct_answer": {"text": "تهران"},
            "max_score": 1,
        },
    ).json()

    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]

    client.post(
        f"/exams/{exam_id}/students/{student_id}/answers",
        json={
            "answers": [
                {
                    "question_id": mc_question["id"],
                    "answer_content": {"selected_option": "زمین"},
                },
                {
                    "question_id": short_answer_question["id"],
                    "answer_content": {"text": "شهر تهران"},
                },
            ]
        },
    )

    return {"exam_id": exam_id, "student_id": student_id}


def test_grade_single_sheet_then_view_results(client: TestClient):
    context = _setup_exam_and_student(client)

    grade_response = client.post(
        f"/exams/{context['exam_id']}/students/{context['student_id']}/grade"
    )
    assert grade_response.status_code == 200
    results = grade_response.json()
    assert len(results) == 2

    # ? سؤال کوتاه‌پاسخ با confidence=55 باید NEEDS_REVIEW باشد
    short_answer_result = next(r for r in results if r["max_score"] == 1 and r["graded_by"] == "ShortAnswerGrader")
    assert short_answer_result["status"] == "needs_review"
    assert short_answer_result["grading_method"] == "llm"

    results_response = client.get(f"/exams/{context['exam_id']}/results")
    assert results_response.status_code == 200
    summary = results_response.json()[0]
    assert summary["total_score"] == 2
    assert summary["needs_review_question_count"] == 1


def test_grade_all_sheets_endpoint(client: TestClient):
    context = _setup_exam_and_student(client)
    response = client.post(f"/exams/{context['exam_id']}/grade")
    assert response.status_code == 200
    assert context["student_id"] in response.json()


def test_review_queue_and_teacher_override_flow(client: TestClient):
    context = _setup_exam_and_student(client)
    client.post(f"/exams/{context['exam_id']}/students/{context['student_id']}/grade")

    review_response = client.get("/review-queue", params={"exam_id": context["exam_id"]})
    assert review_response.status_code == 200
    review_items = review_response.json()
    assert len(review_items) == 1  # فقط سؤال کوتاه‌پاسخ با confidence پایین

    grade_result_id = review_items[0]["id"]
    override_response = client.post(
        f"/review-queue/{grade_result_id}/override",
        json={"final_score": 1, "teacher_reasoning": "معلم تأیید کرد پاسخ درست است"},
    )
    assert override_response.status_code == 200
    assert override_response.json()["status"] == "teacher_overridden"
    assert override_response.json()["grading_method"] == "teacher"

    # ! بعد از Override، دیگر نباید در صف بازبینی باشد
    review_after = client.get("/review-queue", params={"exam_id": context["exam_id"]})
    assert review_after.json() == []


def test_override_rejects_score_above_max(client: TestClient):
    context = _setup_exam_and_student(client)
    client.post(f"/exams/{context['exam_id']}/students/{context['student_id']}/grade")
    review_items = client.get(
        "/review-queue", params={"exam_id": context["exam_id"]}
    ).json()
    grade_result_id = review_items[0]["id"]

    response = client.post(
        f"/review-queue/{grade_result_id}/override",
        json={"final_score": 99, "teacher_reasoning": "اشتباه عمدی"},
    )
    assert response.status_code == 422
