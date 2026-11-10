"""Tests that the real content loads, and that common mistakes give clear errors."""

import shutil
from pathlib import Path

import pytest

from portfolio.content import ContentError, ProjectFile, _parse, load, split_entry

ROOT = Path(__file__).resolve().parents[1]


def test_repository_content_is_valid() -> None:
    """Everything in content/ loads and passes the cross-checks."""
    content = load(ROOT)
    assert content.projects and content.experience


def test_unquoted_bullet_with_colon_gets_a_helpful_error() -> None:
    """A bullet split by YAML at ': ' is explained, not reported as a schema mismatch."""
    data = {"title": "T", "date": "2026-01", "category": "llm", "resume": {"bullets": [{"Built X": "the rest"}]}}
    with pytest.raises(ContentError, match="Wrap the whole bullet in single quotes"):
        _parse(ProjectFile, data, Path("index.md"))


def test_misspelt_field_is_rejected() -> None:
    """Unknown keys are errors, so a typo can't silently drop content."""
    with pytest.raises(ContentError, match="unknown field"):
        _parse(ProjectFile, {"title": "T", "date": "2026-01", "category": "llm", "sumary": "x"}, Path("index.md"))


def test_dates_must_be_year_or_year_month() -> None:
    """Dates like 2026-13 or 26-01 are rejected."""
    for bad in ["2026-13", "26-01", "2026-1"]:
        with pytest.raises(ContentError):
            _parse(ProjectFile, {"title": "T", "date": bad, "category": "llm"}, Path("index.md"))


def test_entry_is_split_into_frontmatter_and_body() -> None:
    """The YAML between the --- lines is data; a --- line inside the body is just part of the body."""
    data, body = split_entry("---\ntitle: T\nskills: [a]\n---\n\nText.\n\n---\n\nMore.\n", Path("index.md"))
    assert data == {"title": "T", "skills": ["a"]}
    assert "Text." in body and "\n---\n" in body and "More." in body


def test_body_keeps_its_line_numbers() -> None:
    """The body is padded so that line N of the body is line N of the file, for render errors."""
    _, body = split_entry("---\ntitle: T\n---\nfirst\nsecond\n", Path("index.md"))
    assert body.splitlines()[3] == "first"  # line 4 of the file


def test_empty_frontmatter_and_missing_body_are_allowed() -> None:
    """A file may have no body, and empty frontmatter reads as no fields rather than as nothing."""
    assert split_entry("---\ntitle: T\n---\n", Path("index.md"))[1].strip() == ""
    assert split_entry("---\n---\n", Path("index.md"))[0] == {}


def test_missing_or_unclosed_frontmatter_is_explained() -> None:
    """A file that doesn't start with --- or never closes it says what is wrong."""
    with pytest.raises(ContentError, match="start with a --- line"):
        split_entry("title: T\n", Path("index.md"))
    with pytest.raises(ContentError, match="never closed"):
        split_entry("---\ntitle: T\n", Path("index.md"))


def test_yaml_error_names_the_line_in_the_file() -> None:
    """A syntax error in the frontmatter is reported at its line in the Markdown file, not in the YAML part."""
    with pytest.raises(ContentError, match=r"index\.md:3: YAML syntax error"):
        split_entry("---\ntitle: T\nbullet: *bold\n---\n", Path("index.md"))


def test_every_paper_has_an_overview_page() -> None:
    """Papers load from content/research/<key>/index.md with their overview as the body."""
    content = load(ROOT)
    assert {pub.key for pub in content.publications} >= {"grokking-review", "grokking-rigidity", "mbert-ner"}
    assert all(pub.page for pub in content.publications)


def copy_content(tmp_path: Path) -> Path:
    """Copy content/ into a temporary repository root and return the root."""
    shutil.copytree(ROOT / "content", tmp_path / "content")
    return tmp_path


def test_thesis_is_a_research_entry_with_its_own_page() -> None:
    """The thesis loads from content/research/ with its degree, and the papers point to it, not to a project."""
    content = load(ROOT)
    thesis = next(t for t in content.theses if t.key == "grokking-thesis")
    assert thesis.page and thesis.degree in content.experience
    assert "grokking-thesis" not in content.projects
    assert {pub.thesis for pub in content.publications if pub.thesis} == {"grokking-thesis"}


def test_thesis_must_name_an_education_entry(tmp_path: Path) -> None:
    """A thesis whose degree is not an education entry is reported, with a suggestion."""
    root = copy_content(tmp_path)
    path = root / "content" / "research" / "grokking-thesis" / "index.md"
    path.write_text(path.read_text().replace("degree: vit-bhopal", "degree: vit-bopal"))
    with pytest.raises(ContentError, match=r"degree: no education entry 'vit-bopal'.*did you mean 'vit-bhopal'"):
        load(root)


def test_paper_must_name_a_real_thesis(tmp_path: Path) -> None:
    """A paper's website.thesis must be the key of a thesis."""
    root = copy_content(tmp_path)
    path = root / "content" / "research" / "grokking-review" / "index.md"
    path.write_text(path.read_text().replace("thesis: grokking-thesis", "thesis: nope"))
    with pytest.raises(ContentError, match="thesis: no thesis 'nope'"):
        load(root)
