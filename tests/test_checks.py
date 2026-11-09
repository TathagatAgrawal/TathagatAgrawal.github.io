"""Tests for the phone-number leak check and the broken-link check."""

from pathlib import Path

from portfolio.checks import find_phone_numbers, link_check


def test_finds_indian_mobile_numbers_in_common_formats() -> None:
    """Numbers written with +91, 0, spaces or dashes are all caught."""
    first, last = "98765", "43210"  # assembled at runtime so this file passes the leak check itself
    for text in [f"+91{first}{last}", f"+91 {first} {last}", f"0{first}-{last}", f"call {first}{last} today"]:
        assert find_phone_numbers(text), text


def test_ignores_numbers_that_are_not_phone_numbers() -> None:
    """Long decimals in result files, years and short numbers are not flagged."""
    for text in ["0.6932422294252155", "-3.365825740962222", "AY 2026-27", "100,000 samples", "1,41,170.00"]:
        assert not find_phone_numbers(text), text


def test_link_check_reports_missing_targets(tmp_path: Path) -> None:
    """A link to a page that wasn't generated is reported; existing pages and anchors are not."""
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects" / "index.html").write_text("ok")
    (tmp_path / "index.html").write_text('<a href="/projects/">x</a> <a href="/missing/">y</a> <a href="#top">z</a>')
    problems = link_check(tmp_path)
    assert problems == ["index.html: broken link /missing/"]
