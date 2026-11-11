from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 11, 10)


def test_today_tomorrow_yesterday() -> None:
    assert parse("today", today=TODAY) == date(2025, 11, 10)
    assert parse("tomorrow", today=TODAY) == date(2025, 11, 11)
    assert parse("yesterday", today=TODAY) == date(2025, 11, 9)


def test_day_after_tomorrow_and_day_before_yesterday() -> None:
    assert parse("the day after tomorrow", today=TODAY) == date(2025, 11, 12)
    assert parse("the day before yesterday", today=TODAY) == date(2025, 11, 8)


@pytest.mark.parametrize(
    "text",
    [
        "December 1st, 2025",
        "December 1, 2025",
        "Dec 1 2025",
        "Dec. 1st, 2025",
        "1 December 2025",
        "the 1st of December, 2025",
        "Monday, December 1st, 2025",
        "december first 2025",
    ],
)
def test_absolute_month_day_year(text: str) -> None:
    assert parse(text, today=TODAY) == date(2025, 12, 1)


@pytest.mark.parametrize("text", ["2025-12-01", "2025/12/01", "12/01/2025", "12/1/25"])
def test_numeric_formats(text: str) -> None:
    assert parse(text, today=TODAY) == date(2025, 12, 1)


def test_missing_year_uses_current_year() -> None:
    assert parse("March 3rd", today=TODAY) == date(2025, 3, 3)


def test_offset_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025", today=TODAY) == date(2025, 11, 26)


def test_compound_offset_after_relative_anchor() -> None:
    assert parse("1 year and 2 months after yesterday", today=TODAY) == date(2027, 1, 9)
    assert parse("1 year, 2 months, and 3 days after today", today=TODAY) == date(
        2027, 1, 13
    )


def test_word_numbers_and_from() -> None:
    assert parse("two weeks from tomorrow", today=TODAY) == date(2025, 11, 25)
    assert parse("a week from today", today=TODAY) == date(2025, 11, 17)
    assert parse("twenty-one days after today", today=TODAY) == date(2025, 12, 1)


def test_in_and_ago() -> None:
    assert parse("in 3 days", today=TODAY) == date(2025, 11, 13)
    assert parse("in a month", today=TODAY) == date(2025, 12, 10)
    assert parse("3 weeks ago", today=TODAY) == date(2025, 10, 20)
    assert parse("3 days from now", today=TODAY) == date(2025, 11, 13)


def test_next_and_last_weekday() -> None:
    assert parse("next Tuesday", today=TODAY) == date(2025, 11, 11)
    assert parse("next Monday", today=TODAY) == date(2025, 11, 17)
    assert parse("last Friday", today=TODAY) == date(2025, 11, 7)
    assert parse("last Monday", today=TODAY) == date(2025, 11, 3)


def test_next_last_unit() -> None:
    assert parse("next week", today=TODAY) == date(2025, 11, 17)
    assert parse("next month", today=TODAY) == date(2025, 12, 10)
    assert parse("last year", today=TODAY) == date(2024, 11, 10)


def test_month_end_clamping() -> None:
    assert parse("1 month after January 31, 2024", today=TODAY) == date(2024, 2, 29)
    assert parse("1 year after February 29, 2024", today=TODAY) == date(2025, 2, 28)


def test_case_and_whitespace_insensitive() -> None:
    assert parse("  NEXT   tuesday ", today=TODAY) == date(2025, 11, 11)


def test_today_defaults_to_current_date() -> None:
    assert parse("today") == date.today()


@pytest.mark.parametrize(
    "text", ["", "   ", "banana", "February 30, 2025", "5 days before", "next blah"]
)
def test_invalid_raises_value_error(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text, today=TODAY)
