from datetime import timedelta

import pytest

from gitsummarizer.windows import parse_window


def test_one_week():
    assert parse_window("1w") == timedelta(weeks=1)


def test_seven_days_equals_one_week():
    assert parse_window("7d") == parse_window("1w")


def test_one_month_is_thirty_days():
    assert parse_window("1m") == timedelta(days=30)


def test_thirty_days():
    assert parse_window("30d") == timedelta(days=30)


def test_case_insensitive():
    assert parse_window("1W") == parse_window("1w")


@pytest.mark.parametrize("bad", ["", "w", "1", "1y", "abc", "-1d", "0d", "1.5w"])
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        parse_window(bad)
