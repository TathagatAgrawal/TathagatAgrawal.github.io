"""Tests that a resume's data applies overrides in the right order and picks what the config says."""

import shutil
from pathlib import Path

import pytest
import yaml

from portfolio.content import ContentError, ExperienceFile, load
from portfolio.resume_data import resume_model, resume_range

ROOT = Path(__file__).resolve().parents[1]


def sections(model: dict, kind: str) -> dict:
    """The one section of the given kind in a resume's data."""
    return next(s for s in model["sections"] if s["kind"] == kind)


def job(**extra: object) -> ExperienceFile:
    """A minimal job with shared bullets, plus whatever overrides the test adds."""
    data = {"type": "work", "role": "Dev", "organisation": "Acme", "start": "2024-01", "bullets": ["shared"], **extra}
    return ExperienceFile.model_validate(data)


def test_bullets_prefer_the_resumes_own_then_the_resumes_then_the_shared_ones() -> None:
    """A resume's own bullets beat the resumes' bullets, which beat the shared ones; the website ignores both."""
    plain = job()
    assert plain.resume_bullets("ml") == ["shared"] and plain.site_bullets() == ["shared"]

    all_resumes = job(resume={"bullets": ["for resumes"]})
    assert all_resumes.resume_bullets("ml") == ["for resumes"]
    assert all_resumes.site_bullets() == ["shared"]

    one = job(resume={"bullets": ["for resumes"], "variants": {"general": {"bullets": ["for general"]}}})
    assert one.resume_bullets("general") == ["for general"]
    assert one.resume_bullets("ml") == ["for resumes"]


def test_website_bullets_replace_the_shared_ones_only_on_the_website() -> None:
    """website.bullets change what the site shows but not what any resume shows."""
    entry = job(website={"bullets": ["for the site"]})
    assert entry.site_bullets() == ["for the site"]
    assert entry.resume_bullets("ml") == ["shared"]


def test_resume_title_prefers_the_variant_then_the_resumes_then_the_role() -> None:
    """The heading on a resume falls back from this resume's title to the shared one to the job's role."""
    entry = job(resume={"title": "Developer", "variants": {"general": {"title": "Dev (short)"}}})
    assert (entry.resume_title("general"), entry.resume_title("ml")) == ("Dev (short)", "Developer")
    assert job().resume_title("ml") == "Dev"


def test_dates_are_formatted_for_a_resume() -> None:
    """A current role says Present, a one-month role shows one date, and a range shows both."""
    assert resume_range("2025-10", None) == "October 2025 – Present"
    assert resume_range("2024-05", "2024-05") == "May 2024"
    assert resume_range("2020", "2025") == "2020 – 2025"


def test_real_resumes_follow_the_config() -> None:
    """Each resume shows the sections, jobs and projects the config lists, with the text converted for Typst."""
    content = load(ROOT)
    for name, config in content.site.resumes.items():
        model = resume_model(content, name)
        assert [s["kind"] for s in model["sections"]] == list(config.sections)
        if "projects" in config.sections:
            titles = [e["title"] for e in sections(model, "projects")["entries"]]
            assert len(titles) == len(config.projects)
    ml = resume_model(content, "ml")
    bullets = sections(ml, "experience")["entries"][0]["bullets"]
    assert any(
        "*improving NDCG\\@3" in b for b in bullets if isinstance(b, str)
    )  # Markdown ** became Typst *, @ escaped


def test_skill_line_can_get_its_own_label_on_one_resume() -> None:
    """The quant resume shows the shared developer-tools line under a different label."""
    content = load(ROOT)
    labels = {
        n: [line["label"] for line in sections(resume_model(content, n), "skills")["lines"]] for n in ("ml", "quant")
    }
    assert labels["ml"][-1] == "Developer and Agentic Tools"
    assert labels["quant"][-1] == "Developer Tools"
    lines = {n: sections(resume_model(content, n), "skills")["lines"][-1]["skills"] for n in ("ml", "quant")}
    assert lines["ml"] == lines["quant"]


def test_text_that_cannot_be_shown_on_a_resume_is_reported(tmp_path: Path) -> None:
    """An image inside a resume bullet is an error that names the file and bullet, not a broken PDF."""
    shutil.copytree(ROOT / "content", tmp_path / "content")
    path = tmp_path / "content" / "experience" / "finlatics.yaml"
    data = yaml.safe_load(path.read_text())
    data["bullets"][0] = "An image ![alt](pic.png) in a bullet"
    path.write_text(yaml.safe_dump(data))
    content = load(tmp_path)
    with pytest.raises(ContentError, match=r"content/experience/finlatics\.yaml: bullets\.0: image is not supported"):
        resume_model(content, "ml")
