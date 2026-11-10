"""Tests that content/config.yaml is checked against the files it names."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from portfolio.content import ContentError, load

ROOT = Path(__file__).resolve().parents[1]


def load_with_config(tmp_path: Path, edit: Callable[[dict], None]):
    """Load a copy of content/ whose config.yaml has been changed by edit."""
    root = tmp_path / str(len(list(tmp_path.iterdir())))  # a fresh copy each time, so one test can load several
    shutil.copytree(ROOT / "content", root / "content")
    path = root / "content" / "config.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    edit(config)
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return load(root)


def test_visibility_and_featured_come_from_the_config(tmp_path: Path) -> None:
    """A project is shown exactly when it is listed under website.projects, and featured ones keep their order."""
    content = load_with_config(tmp_path, lambda c: c["website"].update(featured=["trade-filter-ml", "anuchhed"]))
    assert [p.key for p in content.projects.values() if p.visible] == sorted(content.site.website.projects)
    assert content.site.website.featured == ["trade-filter-ml", "anuchhed"]
    assert not content.projects["chess"].visible


def test_unknown_project_gets_a_suggestion(tmp_path: Path) -> None:
    """A misspelt key in website.projects names the closest real project."""
    with pytest.raises(ContentError, match="no project 'clinic-agnt' \\(did you mean 'clinic-agent'"):
        load_with_config(tmp_path, lambda c: c["website"]["projects"].append("clinic-agnt"))


def test_featured_project_must_be_shown(tmp_path: Path) -> None:
    """Featuring a project that is not on the website is an error."""
    with pytest.raises(ContentError, match="website.featured: no project in website.projects 'chess'"):
        load_with_config(tmp_path, lambda c: c["website"]["featured"].append("chess"))


def test_degree_cannot_go_under_experience(tmp_path: Path) -> None:
    """A resume's experience list takes jobs only, and education takes degrees only."""
    with pytest.raises(ContentError, match="resumes.ml.experience: no job"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"]["experience"].append("vit-bhopal"))


def test_section_and_list_must_agree(tmp_path: Path) -> None:
    """A section with nothing under it, or a list with no section to show it, is reported."""
    with pytest.raises(ContentError, match="has a 'publications' section but publications: is empty"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"].update(publications=[]))
    with pytest.raises(ContentError, match="lists projects: but has no 'projects' section"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"]["sections"].remove("projects"))


def test_published_resume_must_exist(tmp_path: Path) -> None:
    """website.resume must name a resume defined in the config."""
    with pytest.raises(ContentError, match="website.resume: no resume 'nope'"):
        load_with_config(tmp_path, lambda c: c["website"].update(resume="nope"))


def test_layout_needs_units(tmp_path: Path) -> None:
    """Layout sizes are Typst lengths, so a bare number is rejected."""
    with pytest.raises(ContentError, match="expected a length with a unit"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"].update(layout={"margin": 0.5}))


def test_resume_skill_line_must_exist(tmp_path: Path) -> None:
    """A resume that lists a skill line which isn't in skills.yaml is reported, with a suggestion."""
    with pytest.raises(
        ContentError, match=r"resumes\.ml\.skills: no skill line in content/skills\.yaml 'ml-dll'.*ml-dl"
    ):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"]["skills"].append("ml-dll"))


def test_skills_section_needs_lines_and_lines_need_a_section(tmp_path: Path) -> None:
    """A skills section with no lines, or lines with no skills section, is reported."""
    with pytest.raises(ContentError, match="has a 'skills' section but skills: is empty"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"].update(skills=[]))
    with pytest.raises(ContentError, match="lists skills: but has no 'skills' section"):
        load_with_config(tmp_path, lambda c: c["resumes"]["ml"]["sections"].remove("skills"))
