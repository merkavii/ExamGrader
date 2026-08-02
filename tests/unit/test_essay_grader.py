# * ==============================================================================
# *                        Tests: EssayGrader
# * ==============================================================================

from domain.models.enums import AnswerSource, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.enums import GradingStatus
from domain.models.rubric import Rubric, RubricCriterion
from domain.models.student import AnswerContent, StudentAnswer
from grading.graders.essay_grader import EssayGrader
from tests.unit.fakes import FakeLLMClient, RaisingLLMClient


def _essay_question() -> Question:
    rubric = Rubric(
        criteria=[
            RubricCriterion(description="اشاره به نور", points=1),
            RubricCriterion(description="اشاره به آب", points=1),
        ]
    )
    return Question(
        id="q1",
        exam_id="exam-1",
        question_text="فتوسنتز را توضیح دهید",
        question_type=QuestionType.ESSAY,
        correct_answer=CorrectAnswer(essay_reference="گیاهان با نور و آب غذا می‌سازند"),
        rubric=rubric,
        max_score=2,
    )


def _answer(text: str | None) -> StudentAnswer:
    return StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id="q1",
        answer_content=AnswerContent(text=text),
        source=AnswerSource.MANUAL,
    )


def test_essay_grader_sums_criteria_scores_from_llm_response():
    fake_llm = FakeLLMClient(
        fixed_response="""{
            "criteria_scores": [
                {"description": "اشاره به نور", "points_awarded": 1},
                {"description": "اشاره به آب", "points_awarded": 0.5}
            ],
            "reasoning": "پاسخ به نور کامل و به آب ناقص اشاره کرده",
            "confidence": 85
        }"""
    )
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer("گیاهان با نور غذا می‌سازند"))

    assert result.score == 1.5
    assert result.status == GradingStatus.GRADED
    assert result.confidence.grading_confidence == 85


def test_essay_grader_handles_markdown_fenced_json():
    fake_llm = FakeLLMClient(
        fixed_response="""```json
        {
            "criteria_scores": [
                {"description": "اشاره به نور", "points_awarded": 1},
                {"description": "اشاره به آب", "points_awarded": 1}
            ],
            "reasoning": "پاسخ کامل بود",
            "confidence": 95
        }
        ```"""
    )
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer("گیاهان با نور و آب غذا می‌سازند"))
    assert result.score == 2


def test_essay_grader_caps_score_at_max_even_if_llm_overshoots():
    # ! دفاعی: حتی اگر مدل اشتباهاً امتیاز بیشتر از max_score بدهد
    fake_llm = FakeLLMClient(
        fixed_response="""{
            "criteria_scores": [
                {"description": "اشاره به نور", "points_awarded": 5},
                {"description": "اشاره به آب", "points_awarded": 5}
            ],
            "reasoning": "خطای فرضی مدل",
            "confidence": 90
        }"""
    )
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer("پاسخ کامل"))
    assert result.score == 2  # max_score


def test_essay_grader_marks_needs_review_on_low_confidence():
    fake_llm = FakeLLMClient(
        fixed_response="""{
            "criteria_scores": [{"description": "اشاره به نور", "points_awarded": 0.5}],
            "reasoning": "پاسخ مبهم بود",
            "confidence": 40
        }"""
    )
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer("یک پاسخ نامشخص"))
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_essay_grader_marks_needs_review_on_invalid_json():
    fake_llm = FakeLLMClient(fixed_response="این یک پاسخ نامعتبر است، نه JSON")
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer("پاسخی از دانش‌آموز"))
    assert result.status == GradingStatus.NEEDS_REVIEW
    assert result.score == 0


def test_essay_grader_marks_needs_review_on_llm_connection_error():
    result = EssayGrader(RaisingLLMClient()).grade(_essay_question(), _answer("پاسخی از دانش‌آموز"))
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_essay_grader_empty_answer_does_not_call_llm():
    fake_llm = FakeLLMClient(fixed_response="{}")
    result = EssayGrader(fake_llm).grade(_essay_question(), _answer(None))
    assert result.score == 0
    assert fake_llm.last_prompt is None  # ! LLM اصلاً نباید صدا زده شود
