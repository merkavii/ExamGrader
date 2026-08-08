# * ==============================================================================
# *      Integration Test: Answer Extraction API (Full HTTP Flow)
# * ==============================================================================
# ? get_ocr_client اینجا Override می‌شود تا از FakeOCRClient استفاده کند -
# ? دقیقاً همان الگویی که برای get_llm_client/FakeLLMClient در تست‌های قبلی
# ? استفاده شد. این یعنی این تست به نصب بودن بسته زبان Tesseract وابسته نیست.

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_db_session, get_llm_client, get_ocr_client
from app.main import app
from infrastructure.database.models import Base
from ocr.ocr_client import OCRLine
from tests.unit.fakes import FakeLLMClient, FakeOCRClient


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
    app.dependency_overrides[get_ocr_client] = lambda: FakeOCRClient(
        lines=[OCRLine(text="تهران", confidence=90)]
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def _tiny_png_bytes() -> bytes:
    # ? یک PNG سفید ۱۰x۱۰ واقعی و معتبر - برای عبور از imdecode در Backend
    import cv2
    import numpy as np

    image = np.full((10, 10, 3), 255, dtype=np.uint8)
    return cv2.imencode(".png", image)[1].tobytes()


def test_extract_answers_from_image_returns_suggestions(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون"}).json()["id"]
    question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "پایتخت ایران؟",
            "question_type": "short_answer",
            "correct_answer": {"text": "تهران"},
            "max_score": 1,
        },
    ).json()
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]

    response = client.post(
        f"/exams/{exam_id}/students/{student_id}/answers/extract-from-image",
        files={"image": ("sheet.png", io.BytesIO(_tiny_png_bytes()), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["extracted_answers"]) == 1
    assert body["extracted_answers"][0]["question_id"] == question["id"]
    assert body["extracted_answers"][0]["suggested_answer"]["text"] == "تهران"


def test_extract_rejects_non_image_file(client: TestClient):
    exam_id = client.post("/exams", json={"title": "آزمون"}).json()["id"]
    client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "س",
            "question_type": "short_answer",
            "correct_answer": {"text": "ج"},
            "max_score": 1,
        },
    )
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]

    response = client.post(
        f"/exams/{exam_id}/students/{student_id}/answers/extract-from-image",
        files={"image": ("sheet.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400


def test_extract_returns_404_for_unknown_exam(client: TestClient):
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]
    response = client.post(
        f"/exams/does-not-exist/students/{student_id}/answers/extract-from-image",
        files={"image": ("sheet.png", io.BytesIO(_tiny_png_bytes()), "image/png")},
    )
    assert response.status_code == 404


def test_extracted_suggestions_can_be_submitted_via_existing_endpoint(client: TestClient):
    # ? این تست دقیقاً همان مسیر معماری را تأیید می‌کند: استخراج فقط پیشنهاد
    # ? می‌دهد، ثبت نهایی همچنان از همان endpoint دستی موجود (بدون تغییر) است.
    exam_id = client.post("/exams", json={"title": "آزمون"}).json()["id"]
    question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "پایتخت ایران؟",
            "question_type": "short_answer",
            "correct_answer": {"text": "تهران"},
            "max_score": 1,
        },
    ).json()
    student_id = client.post("/students", json={"full_name": "سارا محمدی"}).json()["id"]

    extraction = client.post(
        f"/exams/{exam_id}/students/{student_id}/answers/extract-from-image",
        files={"image": ("sheet.png", io.BytesIO(_tiny_png_bytes()), "image/png")},
    ).json()

    suggested = extraction["extracted_answers"][0]["suggested_answer"]
    submit_response = client.post(
        f"/exams/{exam_id}/students/{student_id}/answers",
        json={
            "answers": [{"question_id": question["id"], "answer_content": suggested}],
            "source": "image",
        },
    )
    assert submit_response.status_code == 201
    assert submit_response.json()[0]["source"] == "image"
