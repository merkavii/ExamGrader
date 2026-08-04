# * ==============================================================================
# *                    Tests: ClassAnalyticsService
# * ==============================================================================
# ? همه اعداد این تست‌ها با محاسبه دستی روی کاغذ تأیید شده‌اند - طبق درخواست
# ? صریح پروژه: "خروجی آماری باید با محاسبه دستی مطابقت داشته باشد".

from domain.models.enums import GradingMethod, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Exam, Question
from domain.models.grading_result import ConfidenceScore, GradeResult
from analytics.class_analytics import ClassAnalyticsService


class _FakeExamRepository:
    """? Test Double ساده به‌جای SqlExamRepository - فقط get_by_id لازم است."""

    def __init__(self, exam: Exam) -> None:
        self._exam = exam

    def get_by_id(self, exam_id: str) -> Exam | None:
        return self._exam if exam_id == self._exam.id else None


class _FakeGradeResultRepository:
    def __init__(self, results: list[GradeResult]) -> None:
        self._results = results

    def get_by_exam(self, exam_id: str) -> list[GradeResult]:
        return [r for r in self._results if r.exam_id == exam_id]


def _result(student_id: str, question_id: str, score: float, max_score: float) -> GradeResult:
    return GradeResult(
        exam_id="exam-1",
        student_id=student_id,
        question_id=question_id,
        score=score,
        max_score=max_score,
        reasoning="دلیل نمونه",
        confidence=ConfidenceScore(grading_confidence=95, final_score=95),
        status=GradingStatus.GRADED,
        grading_method=GradingMethod.RULE_BASED,
        graded_by="TrueFalseGrader",
    )


def _build_exam() -> Exam:
    q1 = Question(
        id="q1",
        exam_id="exam-1",
        question_text="سؤال یک",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
        topic="فیزیک",
    )
    q2 = Question(
        id="q2",
        exam_id="exam-1",
        question_text="سؤال دو",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
        topic="شیمی",
    )
    return Exam(id="exam-1", title="آزمون نمونه", questions=[q1, q2])


def test_class_average_and_extremes_match_manual_calculation():
    # ? دانش‌آموز ۱: q1=1, q2=1 -> مجموع ۲ (۱۰۰٪)
    # ? دانش‌آموز ۲: q1=0, q2=1 -> مجموع ۱ (۵۰٪)
    # ? دانش‌آموز ۳: q1=0, q2=0 -> مجموع ۰ (۰٪)
    # ? میانگین درصد دستی: (100+50+0)/3 = 50
    results = [
        _result("s1", "q1", 1, 1),
        _result("s1", "q2", 1, 1),
        _result("s2", "q1", 0, 1),
        _result("s2", "q2", 1, 1),
        _result("s3", "q1", 0, 1),
        _result("s3", "q2", 0, 1),
    ]
    service = ClassAnalyticsService(_FakeExamRepository(_build_exam()), _FakeGradeResultRepository(results))
    analytics = service.analyze_exam("exam-1")

    assert analytics.participant_count == 3
    assert analytics.average_percentage == 50.0
    assert analytics.highest_score == 2
    assert analytics.lowest_score == 0
    assert sorted(analytics.score_distribution) == [0.0, 50.0, 100.0]


def test_hardest_question_identified_correctly():
    # ? q1: فقط s1 درست پاسخ داد (1 از 3 = 33.33٪ صحیح)
    # ? q2: s1 و s2 درست پاسخ دادند (2 از 3 = 66.67٪ صحیح)
    # ? پس q1 باید سخت‌تر باشد و اول لیست بیاید.
    results = [
        _result("s1", "q1", 1, 1),
        _result("s1", "q2", 1, 1),
        _result("s2", "q1", 0, 1),
        _result("s2", "q2", 1, 1),
        _result("s3", "q1", 0, 1),
        _result("s3", "q2", 0, 1),
    ]
    service = ClassAnalyticsService(_FakeExamRepository(_build_exam()), _FakeGradeResultRepository(results))
    analytics = service.analyze_exam("exam-1")

    assert analytics.question_analytics[0].question_id == "q1"
    assert analytics.question_analytics[0].correct_percentage == round(1 / 3 * 100, 2)
    assert analytics.question_analytics[1].question_id == "q2"
    assert analytics.question_analytics[1].correct_percentage == round(2 / 3 * 100, 2)


def test_topic_breakdown_matches_manual_calculation():
    # ? موضوع "فیزیک" فقط q1 است: میانگین (1+0+0)/3 * 100 = 33.33
    # ? موضوع "شیمی" فقط q2 است: میانگین (1+1+0)/3 * 100 = 66.67
    results = [
        _result("s1", "q1", 1, 1),
        _result("s1", "q2", 1, 1),
        _result("s2", "q1", 0, 1),
        _result("s2", "q2", 1, 1),
        _result("s3", "q1", 0, 1),
        _result("s3", "q2", 0, 1),
    ]
    service = ClassAnalyticsService(_FakeExamRepository(_build_exam()), _FakeGradeResultRepository(results))
    analytics = service.analyze_exam("exam-1")

    assert analytics.topic_breakdown["فیزیک"] == round(1 / 3 * 100, 2)
    assert analytics.topic_breakdown["شیمی"] == round(2 / 3 * 100, 2)


def test_exam_with_no_results_returns_empty_analytics_not_error():
    service = ClassAnalyticsService(_FakeExamRepository(_build_exam()), _FakeGradeResultRepository([]))
    analytics = service.analyze_exam("exam-1")

    assert analytics.participant_count == 0
    assert analytics.question_analytics == []
    assert analytics.topic_breakdown == {}
