# * ==============================================================================
# *          Tests: GradingOrchestrator - Empty Answer Handling (E2E)
# * ==============================================================================
# ? این فایل دقیقاً معیار موفقیتی را تست می‌کند که خواسته شد: برای هر نوع سؤال
# ? و هر سه حالت خالی (None، ""، "   ")، نتیجه باید score=0، status=GRADED،
# ? grading_method=RULE_BASED، reasoning مشخص، و برای سؤالات LLM-based،
# ? هیچ تماسی با LLM نباید رخ دهد.

import pytest

from domain.models.enums import AnswerSource, GradingMethod, GradingStatus, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.rubric import Rubric, RubricCriterion
from domain.models.student import AnswerContent, StudentAnswer
from grading.orchestrator import GradingOrchestrator
from tests.unit.fakes import FakeLLMClient

EXPECTED_REASONING = "دانش‌آموز پاسخی برای این سؤال ثبت نکرده است."


def _answer(question_id: str, answer_content: AnswerContent) -> StudentAnswer:
    return StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id=question_id,
        answer_content=answer_content,
        source=AnswerSource.MANUAL,
    )


def _assert_empty_answer_result(result):
    assert result.score == 0
    assert result.status == GradingStatus.GRADED
    assert result.grading_method == GradingMethod.RULE_BASED
    assert result.reasoning == EXPECTED_REASONING
    assert result.graded_by == "EmptyAnswerHandler"


# * ---------------------------- Multiple Choice ----------------------------

@pytest.mark.parametrize("selected_option", [None, "", "   "])
def test_multiple_choice_empty_answer(selected_option):
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="کدام گزینه سیاره است؟",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer=CorrectAnswer(selected_option="زمین"),
        options=["ماه", "زمین"],
        max_score=2,
    )
    result = GradingOrchestrator().grade_question(
        question, _answer("q1", AnswerContent(selected_option=selected_option))
    )
    _assert_empty_answer_result(result)


# * ------------------------------ True / False ------------------------------

@pytest.mark.parametrize("selected_option", [None, "", "   "])
def test_true_false_empty_answer(selected_option):
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="آب یخ می‌زند؟",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    result = GradingOrchestrator().grade_question(
        question, _answer("q1", AnswerContent(selected_option=selected_option))
    )
    _assert_empty_answer_result(result)


# * -------------------------------- Numeric ----------------------------------

def test_numeric_empty_answer():
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="شتاب جاذبه زمین؟",
        question_type=QuestionType.NUMERIC,
        correct_answer=CorrectAnswer(numeric_value=9.81),
        numeric_tolerance=0.05,
        max_score=1,
    )
    result = GradingOrchestrator().grade_question(
        question, _answer("q1", AnswerContent(numeric_value=None))
    )
    _assert_empty_answer_result(result)


# * ------------------------------ Short Answer --------------------------------

@pytest.mark.parametrize("text", [None, "", "   "])
def test_short_answer_empty_answer_does_not_call_llm(text):
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="پایتخت ایران؟",
        question_type=QuestionType.SHORT_ANSWER,
        correct_answer=CorrectAnswer(text="تهران"),
        max_score=1,
    )
    fake_llm = FakeLLMClient(fixed_response="این پاسخ نباید هیچ‌وقت خوانده شود")
    result = GradingOrchestrator(llm_client=fake_llm).grade_question(
        question, _answer("q1", AnswerContent(text=text))
    )
    _assert_empty_answer_result(result)
    assert fake_llm.last_prompt is None  # ! تضمین اصلی: LLM هرگز صدا زده نشد


# * ---------------------------------- Essay ------------------------------------

@pytest.mark.parametrize("text", [None, "", "   "])
def test_essay_empty_answer_does_not_call_llm(text):
    rubric = Rubric(
        criteria=[
            RubricCriterion(description="اشاره به نور", points=1),
            RubricCriterion(description="اشاره به آب", points=1),
        ]
    )
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="فتوسنتز را توضیح دهید",
        question_type=QuestionType.ESSAY,
        correct_answer=CorrectAnswer(essay_reference="گیاهان با نور و آب غذا می‌سازند"),
        rubric=rubric,
        max_score=2,
    )
    fake_llm = FakeLLMClient(fixed_response="این پاسخ نباید هیچ‌وقت خوانده شود")
    result = GradingOrchestrator(llm_client=fake_llm).grade_question(
        question, _answer("q1", AnswerContent(text=text))
    )
    _assert_empty_answer_result(result)
    assert fake_llm.last_prompt is None  # ! تضمین اصلی: LLM هرگز صدا زده نشد


# * --------------------- عدم توقف تصحیح در صورت پاسخ خالی ---------------------

def test_empty_answer_does_not_raise_even_for_unsupported_question_type():
    # ? حتی برای نوعی که هنوز Grader ندارد (MATCHING)، پاسخ خالی نباید خطا بدهد
    # ? چون تشخیص "خالی" اصلاً به وجود Grader وابسته نیست.
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="موارد را وصل کنید",
        question_type=QuestionType.MATCHING,
        correct_answer=CorrectAnswer(matching_pairs={"1": "A"}),
        max_score=3,
    )
    result = GradingOrchestrator().grade_question(
        question, _answer("q1", AnswerContent(matching_pairs=None))
    )
    _assert_empty_answer_result(result)
