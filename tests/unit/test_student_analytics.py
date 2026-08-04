# * ==============================================================================
# *                   Tests: StudentAnalyticsService
# * ==============================================================================

from datetime import datetime, timedelta, timezone

from domain.models.enums import GradingMethod, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.grading_result import ConfidenceScore, GradeResult
from analytics.student_analytics import StudentAnalyticsService


class _FakeExamRepository:
    def __init__(self, exams: list[Exam]) -> None:
        self._exams_by_id = {exam.id: exam for exam in exams}
        self._questions_by_id = {
            question.id: question for exam in exams for question in exam.questions
        }

    def get_by_id(self, exam_id: str) -> Exam | None:
        return self._exams_by_id.get(exam_id)

    def get_question(self, question_id: str) -> Question | None:
        return self._questions_by_id.get(question_id)


class _FakeGradeResultRepository:
    def __init__(self, results: list[GradeResult]) -> None:
        self._results = results

    def get_by_student(self, student_id: str) -> list[GradeResult]:
        return [r for r in self._results if r.student_id == student_id]

    def get_by_student_and_exam(self, student_id: str, exam_id: str) -> list[GradeResult]:
        return [
            r for r in self._results if r.student_id == student_id and r.exam_id == exam_id
        ]


def _result(exam_id: str, question_id: str, score: float, max_score: float) -> GradeResult:
    return GradeResult(
        exam_id=exam_id,
        student_id="s1",
        question_id=question_id,
        score=score,
        max_score=max_score,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=95, final_score=95),
        status=GradingStatus.GRADED,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )


def _question(question_id: str, exam_id: str, topic: str | None) -> Question:
    return Question(
        id=question_id,
        exam_id=exam_id,
        question_text="سؤال",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
        topic=topic,
    )


def test_exam_history_is_sorted_oldest_to_newest():
    now = datetime.now(timezone.utc)
    old_exam = Exam(id="exam-old", title="آزمون قدیمی", created_at=now - timedelta(days=10))
    new_exam = Exam(id="exam-new", title="آزمون جدید", created_at=now)

    results = [_result("exam-new", "q-new", 1, 1), _result("exam-old", "q-old", 1, 1)]
    service = StudentAnalyticsService(
        _FakeExamRepository([old_exam, new_exam]), _FakeGradeResultRepository(results)
    )

    analytics = service.analyze_student("s1")

    assert [entry.exam_id for entry in analytics.exam_history] == ["exam-old", "exam-new"]


def test_overall_average_matches_manual_calculation():
    # ? آزمون ۱: 1/1 -> ۱۰۰٪   آزمون ۲: 0/1 -> ۰٪
    # ? میانگین وزنی دستی: (1+0)/(1+1) * 100 = 50
    now = datetime.now(timezone.utc)
    exam1 = Exam(id="exam-1", title="آزمون یک", created_at=now)
    exam2 = Exam(id="exam-2", title="آزمون دو", created_at=now + timedelta(days=1))

    results = [_result("exam-1", "q1", 1, 1), _result("exam-2", "q2", 0, 1)]
    service = StudentAnalyticsService(
        _FakeExamRepository([exam1, exam2]), _FakeGradeResultRepository(results)
    )

    analytics = service.analyze_student("s1")
    assert analytics.overall_average_percentage == 50.0


def test_trend_detects_improvement():
    now = datetime.now(timezone.utc)
    exam1 = Exam(id="exam-1", title="آزمون یک", created_at=now)
    exam2 = Exam(id="exam-2", title="آزمون دو", created_at=now + timedelta(days=1))

    # ? آزمون اول ۰٪، آزمون دوم ۱۰۰٪ -> اختلاف ۱۰۰ > آستانه ۵ -> improving
    results = [_result("exam-1", "q1", 0, 1), _result("exam-2", "q2", 1, 1)]
    service = StudentAnalyticsService(
        _FakeExamRepository([exam1, exam2]), _FakeGradeResultRepository(results)
    )

    assert service.analyze_student("s1").trend == "improving"


def test_trend_insufficient_data_with_single_exam():
    now = datetime.now(timezone.utc)
    exam1 = Exam(id="exam-1", title="آزمون یک", created_at=now)
    results = [_result("exam-1", "q1", 1, 1)]
    service = StudentAnalyticsService(
        _FakeExamRepository([exam1]), _FakeGradeResultRepository(results)
    )

    assert service.analyze_student("s1").trend == "insufficient_data"


def test_topic_breakdown_uses_question_topic_across_exams():
    now = datetime.now(timezone.utc)
    exam1 = Exam(
        id="exam-1",
        title="آزمون یک",
        created_at=now,
        questions=[_question("q1", "exam-1", "فیزیک")],
    )
    exam2 = Exam(
        id="exam-2",
        title="آزمون دو",
        created_at=now,
        questions=[_question("q2", "exam-2", "فیزیک")],
    )
    results = [_result("exam-1", "q1", 1, 1), _result("exam-2", "q2", 0, 1)]
    service = StudentAnalyticsService(
        _FakeExamRepository([exam1, exam2]), _FakeGradeResultRepository(results)
    )

    analytics = service.analyze_student("s1")
    # ? میانگین دستی موضوع فیزیک روی هر دو آزمون: (100 + 0) / 2 = 50
    assert analytics.topic_breakdown["فیزیک"] == 50.0


def test_compare_to_class_computes_correct_difference():
    now = datetime.now(timezone.utc)
    exam1 = Exam(id="exam-1", title="آزمون یک", created_at=now)
    results = [_result("exam-1", "q1", 1, 1)]  # ۱۰۰٪
    service = StudentAnalyticsService(
        _FakeExamRepository([exam1]), _FakeGradeResultRepository(results)
    )

    comparison = service.compare_to_class("s1", "exam-1", class_average_percentage=70)
    assert comparison.student_percentage == 100.0
    assert comparison.class_average_percentage == 70
    assert comparison.difference == 30.0
