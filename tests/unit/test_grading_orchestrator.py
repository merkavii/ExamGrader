# * ==============================================================================
# *                     Tests: GradingOrchestrator
# * ==============================================================================

import pytest

from domain.models.enums import AnswerSource, QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.student import AnswerContent, StudentAnswer
from grading.orchestrator import GradingOrchestrator, UnsupportedQuestionTypeError


def test_orchestrator_routes_multiple_choice_to_correct_grader():
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="کدام گزینه سیاره است؟",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer=CorrectAnswer(selected_option="زمین"),
        options=["ماه", "زمین"],
        max_score=2,
    )
    answer = StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id="q1",
        answer_content=AnswerContent(selected_option="زمین"),
        source=AnswerSource.MANUAL,
    )

    result = GradingOrchestrator().grade_question(question, answer)

    assert result.graded_by == "MultipleChoiceGrader"
    assert result.score == 2


def test_orchestrator_raises_for_unsupported_question_type():
    # ! ESSAY هنوز در فاز ۲ پشتیبانی نمی‌شود - باید خطای صریح بدهد، نه سکوت
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="فتوسنتز را توضیح دهید",
        question_type=QuestionType.SHORT_ANSWER,
        correct_answer=CorrectAnswer(text="نور و آب"),
        max_score=1,
    )
    answer = StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id="q1",
        answer_content=AnswerContent(text="نور و آب"),
        source=AnswerSource.MANUAL,
    )

    with pytest.raises(UnsupportedQuestionTypeError):
        GradingOrchestrator().grade_question(question, answer)


def test_orchestrator_rejects_mismatched_question_and_answer():
    question = Question(
        id="q1",
        exam_id="exam-1",
        question_text="آب یخ می‌زند؟",
        question_type=QuestionType.TRUE_FALSE,
        correct_answer=CorrectAnswer(selected_option="true"),
        max_score=1,
    )
    mismatched_answer = StudentAnswer(
        exam_id="exam-1",
        student_id="s1",
        question_id="q999",  # ! عمداً اشتباه
        answer_content=AnswerContent(selected_option="true"),
        source=AnswerSource.MANUAL,
    )

    with pytest.raises(ValueError):
        GradingOrchestrator().grade_question(question, mismatched_answer)
