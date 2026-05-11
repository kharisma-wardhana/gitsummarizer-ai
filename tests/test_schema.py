from datetime import date

import pytest
from pydantic import ValidationError

from gitsummarizer.schema import (
    Category,
    Difficulty,
    Initiative,
    Priority,
    Roadmap,
    Status,
)


def _initiative(**overrides):
    base = dict(
        initiative="Auth Refactor",
        repositories=["group/project"],
        description="Migrated JWT logic to OAuth2",
        category=Category.SECURITY,
        weight=5,
        status=Status.CLOSED,
        priority=Priority.HIGH,
        start_date=date(2026, 4, 1),
        finish_date=date(2026, 4, 5),
        output="Enhanced Security",
        difficulty=Difficulty.HARD,
    )
    base.update(overrides)
    return Initiative(**base)


def test_roadmap_round_trips_through_json():
    rm = Roadmap(
        repository="group/project",
        repositories=["group/project"],
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 8),
        initiatives=[_initiative()],
    )
    payload = rm.model_dump_json()
    rebuilt = Roadmap.model_validate_json(payload)
    assert rebuilt == rm


def test_invalid_weight_rejected():
    with pytest.raises(ValidationError):
        _initiative(weight=4)  # not Fibonacci


def test_invalid_category_rejected():
    with pytest.raises(ValidationError):
        Initiative(
            initiative="x",
            description="y",
            category="UI/UX",  # not in enum
            weight=1,
            status=Status.OPEN,
            priority=Priority.LOW,
            finish_date=date(2026, 1, 1),
            output="z",
            difficulty=Difficulty.EASY,
        )


def test_enum_values_are_display_strings():
    assert Status.IN_PROGRESS.value == "In Progress"
    assert Category.SYSTEM_PERFORMANCE.value == "System Performance"
    assert Priority.HIGH.value == "High"


def test_start_date_defaults_to_finish_date_when_omitted():
    it = Initiative(
        initiative="x",
        description="y",
        category=Category.OTHERS,
        weight=1,
        status=Status.CLOSED,
        priority=Priority.LOW,
        finish_date=date(2026, 4, 5),
        output="z",
        difficulty=Difficulty.EASY,
    )
    assert it.start_date == date(2026, 4, 5)


def test_initiative_repositories_defaults_to_empty_list():
    it = Initiative(
        initiative="x",
        description="y",
        category=Category.OTHERS,
        weight=1,
        status=Status.CLOSED,
        priority=Priority.LOW,
        finish_date=date(2026, 4, 5),
        output="z",
        difficulty=Difficulty.EASY,
    )
    assert it.repositories == []


def test_roadmap_repositories_defaults_to_empty_list():
    rm = Roadmap(
        repository="group/project",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 8),
        initiatives=[],
    )
    assert rm.repositories == []
