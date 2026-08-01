# * ==============================================================================
# *              Integration Test: Full Manual Input Flow
# * ==============================================================================
# ? هدف: تضمین این‌که از طریق API واقعی (نه صدا زدن مستقیم Repository) می‌توان
# ? یک آزمون کامل ساخت، سؤال اضافه کرد، دانش‌آموز ثبت کرد، پاسخ او را ثبت کرد
# ? و در نهایت وضعیت برگه را مشاهده کرد - دقیقاً همان مسیر معیار موفقیت فاز ۱.
#
# ! از یک دیتابیس SQLite in-memory مجزا برای هر تست استفاده می‌شود تا تست‌ها
# ! به فایل واقعی exam_grader.db دست نزنند و از هم مستقل بمانند.

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
    # ? StaticPool + همان connection یعنی چند session مختلف در طول یک تست
    # ? هنوز به یک دیتابیس in-memory واحد وصل می‌مانند (پیش‌فرض SQLite in-memory
    # ? هر اتصال جدید را یک دیتابیس خالی جدا می‌بیند).
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


def test_full_manual_exam_flow(client: TestClient):
    # * ۱. ساخت آزمون
    exam_response = client.post("/exams", json={"title": "آزمون علوم پایه هفتم"})
    assert exam_response.status_code == 201
    exam_id = exam_response.json()["id"]

    # * ۲. افزودن یک سؤال چهارگزینه‌ای
    mc_question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "کدام گزینه سیاره است؟",
            "question_type": "multiple_choice",
            "correct_answer": {"selected_option": "زمین"},
            "options": ["ماه", "زمین", "خورشید", "ستاره"],
            "max_score": 2,
        },
    )
    assert mc_question.status_code == 201
    mc_question_id = mc_question.json()["id"]

    # * ۳. افزودن یک سؤال عددی
    numeric_question = client.post(
        f"/exams/{exam_id}/questions",
        json={
            "question_text": "شتاب جاذبه زمین چند متر بر مجذور ثانیه است؟",
            "question_type": "numeric",
            "correct_answer": {"numeric_value": 9.81},
            "numeric_tolerance": 0.05,
            "max_score": 1,
        },
    )
    assert numeric_question.status_code == 201
    numeric_question_id = numeric_question.json()["id"]

    # * ۴. بازخوانی سؤال‌ها
    questions = client.get(f"/exams/{exam_id}/questions")
    assert questions.status_code == 200
    assert len(questions.json()) == 2

    # * ۵. ثبت دانش‌آموز
    student_response = client.post("/students", json={"full_name": "سارا محمدی"})
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    # * ۶. ثبت پاسخ‌های او برای هر دو سؤال (یک برگه کامل)
    submit_response = client.post(
        f"/exams/{exam_id}/students/{student_id}/answers",
        json={
            "answers": [
                {
                    "question_id": mc_question_id,
                    "answer_content": {"selected_option": "زمین"},
                },
                {
                    "question_id": numeric_question_id,
                    "answer_content": {"numeric_value": 9.8},
                },
            ]
        },
    )
    assert submit_response.status_code == 201
    assert len(submit_response.json()) == 2

    # * ۷. بازخوانی برگه دانش‌آموز
    sheet = client.get(f"/exams/{exam_id}/students/{student_id}/answers")
    assert sheet.status_code == 200
    assert len(sheet.json()) == 2

    # * ۸. بررسی وضعیت برگه‌ها از دید معلم (تب Sheets)
    statuses = client.get(f"/exams/{exam_id}/sheets")
    assert statuses.status_code == 200
    assert statuses.json() == [
        {
            "student_id": student_id,
            "student_full_name": "سارا محمدی",
            "answered_questions": 2,
            "total_questions": 2,
        }
    ]


def test_submit_answer_for_unrelated_question_is_rejected(client: TestClient):
    # ! تلاش برای ثبت پاسخ به سؤالی که به این آزمون تعلق ندارد باید رد شود
    exam_a = client.post("/exams", json={"title": "آزمون A"}).json()
    exam_b = client.post("/exams", json={"title": "آزمون B"}).json()

    question_in_b = client.post(
        f"/exams/{exam_b['id']}/questions",
        json={
            "question_text": "درست یا غلط: آب در صفر درجه یخ می‌زند؟",
            "question_type": "true_false",
            "correct_answer": {"selected_option": "true"},
            "max_score": 1,
        },
    ).json()

    student = client.post("/students", json={"full_name": "علی رضایی"}).json()

    response = client.post(
        f"/exams/{exam_a['id']}/students/{student['id']}/answers",
        json={
            "answers": [
                {
                    "question_id": question_in_b["id"],
                    "answer_content": {"selected_option": "true"},
                }
            ]
        },
    )
    assert response.status_code == 400
