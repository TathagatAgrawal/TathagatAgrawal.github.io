"""Tests that the real content loads, and that common mistakes give clear errors."""

from pathlib import Path

import pytest

from portfolio.content import ContentError, ProjectFile, _parse, load

ROOT = Path(__file__).resolve().parents[1]


def test_repository_content_is_valid() -> None:
    """Everything in content/ loads and passes the cross-checks."""
    content = load(ROOT)
    assert content.projects and content.experience


def test_unquoted_bullet_with_colon_gets_a_helpful_error() -> None:
    """A bullet split by YAML at ': ' is explained, not reported as a schema mismatch."""
    data = {"title": "T", "date": "2026-01", "category": "llm", "resume": {"bullets": [{"Built X": "the rest"}]}}
    with pytest.raises(ContentError, match="Wrap the whole bullet in single quotes"):
        _parse(ProjectFile, data, Path("p.yaml"))


def test_misspelt_field_is_rejected() -> None:
    """Unknown keys are errors, so a typo can't silently drop content."""
    with pytest.raises(ContentError, match="unknown field"):
        _parse(ProjectFile, {"title": "T", "date": "2026-01", "category": "llm", "sumary": "x"}, Path("p.yaml"))


def test_dates_must_be_year_or_year_month() -> None:
    """Dates like 2026-13 or 26-01 are rejected."""
    for bad in ["2026-13", "26-01", "2026-1"]:
        with pytest.raises(ContentError):
            _parse(ProjectFile, {"title": "T", "date": bad, "category": "llm"}, Path("p.yaml"))
