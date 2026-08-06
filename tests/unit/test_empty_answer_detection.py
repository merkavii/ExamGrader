# * ==============================================================================
# *              Tests: is_blank_text / is_answer_empty (Central Logic)
# * ==============================================================================

import pytest

from domain.models.enums import QuestionType
from domain.models.student import AnswerContent
from grading.empty_answer import is_answer_empty, is_blank_text


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_is_blank_text_detects_all_blank_variants(value):
    assert is_blank_text(value) is True


@pytest.mark.parametrize("value", ["a", "تهران", " تهران ", "0"])
def test_is_blank_text_rejects_non_blank_values(value):
    assert is_blank_text(value) is False


@pytest.mark.parametrize("selected_option", [None, "", "   "])
def test_multiple_choice_and_true_false_treat_blank_selected_option_as_empty(
    selected_option,
):
    content = AnswerContent(selected_option=selected_option)
    assert is_answer_empty(QuestionType.MULTIPLE_CHOICE, content) is True
    assert is_answer_empty(QuestionType.TRUE_FALSE, content) is True


def test_multiple_choice_with_real_answer_is_not_empty():
    content = AnswerContent(selected_option="زمین")
    assert is_answer_empty(QuestionType.MULTIPLE_CHOICE, content) is False


def test_numeric_only_none_is_empty_zero_is_not():
    assert is_answer_empty(QuestionType.NUMERIC, AnswerContent(numeric_value=None)) is True
    assert is_answer_empty(QuestionType.NUMERIC, AnswerContent(numeric_value=0)) is False


@pytest.mark.parametrize("text", [None, "", "   "])
def test_short_answer_and_essay_treat_blank_text_as_empty(text):
    content = AnswerContent(text=text)
    assert is_answer_empty(QuestionType.SHORT_ANSWER, content) is True
    assert is_answer_empty(QuestionType.ESSAY, content) is True
    assert is_answer_empty(QuestionType.FILL_IN_BLANK, content) is True


def test_short_answer_with_real_text_is_not_empty():
    content = AnswerContent(text="تهران")
    assert is_answer_empty(QuestionType.SHORT_ANSWER, content) is False


def test_matching_with_no_pairs_is_empty():
    assert is_answer_empty(QuestionType.MATCHING, AnswerContent(matching_pairs=None)) is True
    assert is_answer_empty(QuestionType.MATCHING, AnswerContent(matching_pairs={})) is True
    assert (
        is_answer_empty(QuestionType.MATCHING, AnswerContent(matching_pairs={"1": "A"}))
        is False
    )
