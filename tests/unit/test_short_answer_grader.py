# * ==============================================================================
# *                      Tests: ShortAnswerGrader
# * ==============================================================================

from domain.models.enums import AnswerSource, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.student import AnswerContent, StudentAnswer
from grading.graders.short_answer_grader import ShortAnswerGrader
from tests.unit.fakes import FakeLLMClient, RaisingLLMClient


def _short_answer_question() -> Question:
    return Question(
        id="q1",
        exam_id="exam-1",
        question_text="پایتخت ایران؟",
        question_type=QuestionType.SHORT_ANSWER,
        correct_answer=CorrectAnswer(text="تهران"),
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


def test_semantically_correct_but_differently_worded_answer_gets_full_score():
    # ? دقیقاً همان مثالی که در ابتدای پروژه گفته شد: "شهر تهران" باید با
    # ? "تهران" معادل باشد - این چیزی است که مقایسه رشته‌ای ساده نمی‌تواند بدهد.
    fake_llm = FakeLLMClient(
        fixed_response='{"is_correct": true, "reasoning": "هر دو به یک شهر اشاره دارند", "confidence": 92}'
    )
    result = ShortAnswerGrader(fake_llm).grade(_short_answer_question(), _answer("شهر تهران"))
    assert result.score == 2
    assert result.status == GradingStatus.GRADED


def test_incorrect_answer_gets_zero():
    fake_llm = FakeLLMClient(
        fixed_response='{"is_correct": false, "reasoning": "پاسخ نادرست است", "confidence": 95}'
    )
    result = ShortAnswerGrader(fake_llm).grade(_short_answer_question(), _answer("اصفهان"))
    assert result.score == 0


def test_low_confidence_response_needs_review():
    fake_llm = FakeLLMClient(
        fixed_response='{"is_correct": true, "reasoning": "نامشخص", "confidence": 55}'
    )
    result = ShortAnswerGrader(fake_llm).grade(_short_answer_question(), _answer("پاسخ مبهم"))
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_connection_error_needs_review():
    result = ShortAnswerGrader(RaisingLLMClient()).grade(
        _short_answer_question(), _answer("تهران")
    )
    assert result.status == GradingStatus.NEEDS_REVIEW


def test_empty_answer_does_not_call_llm():
    fake_llm = FakeLLMClient(fixed_response="{}")
    result = ShortAnswerGrader(fake_llm).grade(_short_answer_question(), _answer(None))
    assert result.score == 0
    assert fake_llm.last_prompt is None
