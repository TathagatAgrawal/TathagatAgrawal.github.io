"""Tests that every resume defined in content/config.yaml compiles from the real content."""

from pathlib import Path

import pytest

from portfolio.content import load
from portfolio.resume import compile_resume

ROOT = Path(__file__).resolve().parents[1]
CONTENT = load(ROOT)


@pytest.mark.parametrize("name", sorted(CONTENT.site.resumes))
def test_resume_compiles(name: str) -> None:
    """The resume is built from its entry in the config and the content files, and produces a PDF."""
    assert compile_resume(CONTENT, name).startswith(b"%PDF")


def test_unknown_resume_is_reported() -> None:
    """Asking for a resume that is not in the config fails with the names that are."""
    with pytest.raises(RuntimeError, match="no resume called 'nope'; the resumes are"):
        compile_resume(CONTENT, "nope")
