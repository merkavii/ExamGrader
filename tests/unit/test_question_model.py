# * ==============================================================================
# *                      Tests: Question validation rules
# * ==============================================================================
# ? هدف این تست‌ها: اطمینان از این‌که هیچ Question نامعتبری وارد Canonical Schema
# ? نمی‌شود - مستقل از این‌که از کجا آمده باشد (دستی یا عکس).

import pytest
from pydantic import ValidationError

from domain.models.enums import QuestionType
from domain.models.exam import CorrectAnswer, Question
from domain.models.rubric import Rubric, RubricCriterion


def test_valid_multiple_choice_question():
    question = Question(
        exam_id="exam-1",
        question_text="پایتخت ایران؟",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer=CorrectAnswer(selected_option="B"),
        options=["A", "B", "C", "D"],
        max_score=2,
    )
    assert question.correct_answer.selected_option == "B"


def test_multiple_choice_without_options_fails():
    with pytest.raises(ValidationError):
        Question(
            exam_id="exam-1",
            question_text="پایتخت ایران؟",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer=CorrectAnswer(selected_option="B"),
            max_score=2,
        )


def test_multiple_choice_answer_not_in_options_fails():
    with pytest.raises(ValidationError):
        Question(
            exam_id="exam-1",
            question_text="پایتخت ایران؟",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer=CorrectAnswer(selected_option="Z"),
            options=["A", "B", "C", "D"],
            max_score=2,
        )


def test_numeric_question_requires_tolerance():
    with pytest.raises(ValidationError):
        Question(
            exam_id="exam-1",
            question_text="شتاب جاذبه زمین چند است؟",
            question_type=QuestionType.NUMERIC,
            correct_answer=CorrectAnswer(numeric_value=9.81),
            max_score=1,
            # ! numeric_tolerance عمداً حذف شده تا خطا را بررسی کنیم
        )


def test_valid_numeric_question():
    question = Question(
        exam_id="exam-1",
        question_text="شتاب جاذبه زمین چند است؟",
        question_type=QuestionType.NUMERIC,
        correct_answer=CorrectAnswer(numeric_value=9.81),
        numeric_tolerance=0.05,
        max_score=1,
    )
    assert question.numeric_tolerance == 0.05


def test_essay_question_requires_rubric_matching_max_score():
    rubric = Rubric(
        criteria=[
            RubricCriterion(description="اشاره به نور", points=1),
            RubricCriterion(description="اشاره به آب", points=1),
        ]
    )
    # ! جمع rubric = 2 اما max_score = 3 -> باید خطا بدهد
    with pytest.raises(ValidationError):
        Question(
            exam_id="exam-1",
            question_text="فتوسنتز را توضیح دهید",
            question_type=QuestionType.ESSAY,
            correct_answer=CorrectAnswer(essay_reference="گیاهان با نور و آب غذا می‌سازند"),
            rubric=rubric,
            max_score=3,
        )


def test_valid_essay_question():
    rubric = Rubric(
        criteria=[
            RubricCriterion(description="اشاره به نور", points=1),
            RubricCriterion(description="اشاره به آب", points=1),
        ]
    )
    question = Question(
        exam_id="exam-1",
        question_text="فتوسنتز را توضیح دهید",
        question_type=QuestionType.ESSAY,
        correct_answer=CorrectAnswer(essay_reference="گیاهان با نور و آب غذا می‌سازند"),
        rubric=rubric,
        max_score=2,
    )
    assert question.rubric.total_points == question.max_score


def test_matching_question_requires_pairs():
    with pytest.raises(ValidationError):
        Question(
            exam_id="exam-1",
            question_text="موارد را وصل کنید",
            question_type=QuestionType.MATCHING,
            correct_answer=CorrectAnswer(),
            max_score=3,
        )
