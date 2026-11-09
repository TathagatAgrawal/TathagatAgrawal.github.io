"""Load and validate everything in content/ into typed objects.

The website build reads these objects. The resume templates read the same YAML files directly with
Typst, so the models here also act as the schema that keeps those files readable by the resume.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
DATE_PATTERN = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")


class ContentError(Exception):
    """A problem in a content file, reported with the file and field or line it came from."""


class Strict(BaseModel):
    """Base model that rejects unknown fields, so a misspelt key is an error instead of ignored."""

    model_config = ConfigDict(extra="forbid")


def check_date(value: object) -> str | None:
    """Accept a year (2025) or a year and month (2025-08) and return it as a string."""
    if value is None:
        return None
    text = str(value)
    if not DATE_PATTERN.match(text):
        raise ValueError(f"dates are written YYYY or YYYY-MM, got {text!r}")
    return text


def format_date(value: str | None, *, month: bool = True) -> str:
    """Turn "2026-09" into "September 2026" (or "2026" when month is False or absent)."""
    if not value:
        return ""
    year, _, mon = value.partition("-")
    if mon and month:
        return f"{MONTHS[int(mon) - 1]} {year}"
    return year


def date_key(value: str | None) -> tuple[int, int]:
    """Sort key for a YYYY or YYYY-MM date; a missing date sorts last."""
    if not value:
        return (0, 0)
    year, _, mon = value.partition("-")
    return (int(year), int(mon or 0))


class Link(Strict):
    """A labelled external link."""

    label: str
    url: str


class NestedBullet(Strict):
    """A resume bullet with sub-bullets underneath it."""

    text: str
    bullets: list[str]


Bullet = str | NestedBullet


class ResumeOverride(Strict):
    """Resume fields replaced for one resume variant (for example the one-page general resume)."""

    title: str | None = None
    tech: str | None = None
    bullets: list[Bullet] | None = None
    short: str | None = None
    link: Link | None = None
    summary: str | None = None


class ProjectWebsite(Strict):
    """The website-only fields of a project; the page body lives in page.md beside project.yaml."""

    summary: str
    result: str | None = None
    status: str = "Complete"
    featured: bool = False
    hidden: bool = False


class ProjectResume(Strict):
    """The resume-only fields of a project, written in Typst markup."""

    title: str | None = None
    tech: str | None = None
    bullets: list[Bullet] = []
    short: str | None = None
    link: Link | None = None
    variants: dict[str, ResumeOverride] = {}


class ProjectFile(Strict):
    """The contents of content/projects/<key>/project.yaml."""

    title: str
    date: str
    category: str
    repository: str | None = None
    private: bool = False
    skills: list[str] = []
    links: list[Link] = []
    website: ProjectWebsite | None = None
    resume: ProjectResume | None = None

    _check_date = field_validator("date", mode="before")(check_date)


class ExperienceWebsite(Strict):
    """Website fields of a job or degree: a home-page summary, Markdown bullets, a related project."""

    summary: str | None = None
    bullets: list[str] = []
    project: str | None = None


class ExperienceResume(Strict):
    """Resume bullets of a job or degree, in Typst markup, with optional per-variant replacements."""

    title: str | None = None
    bullets: list[Bullet] = []
    variants: dict[str, ResumeOverride] = {}


class ExperienceFile(Strict):
    """The contents of content/experience/<key>.yaml."""

    type: Literal["work", "education"]
    role: str
    organisation: str
    location: str | None = None
    start: str
    end: str | None = None
    grade: str | None = None
    thesis: str | None = None
    skills: list[str] = []
    website: ExperienceWebsite | None = None
    resume: ExperienceResume | None = None

    _check_dates = field_validator("start", "end", mode="before")(check_date)


class PublicationWebsite(Strict):
    """Website fields of a paper."""

    summary: str | None = None
    project: str | None = None


class PublicationResume(Strict):
    """Resume fields of a paper: a shorter title if needed, and a note after the citation (Typst markup)."""

    title: str | None = None
    note: str | None = None


class Publication(Strict):
    """One paper in content/publications.yaml."""

    key: str
    authors: list[str]
    year: int
    title: str
    venue: str
    url: str | None = None
    url_label: str = "Paper link"
    website: PublicationWebsite = PublicationWebsite()
    resume: PublicationResume = PublicationResume()


class Certification(Strict):
    """One certificate in content/certifications.yaml."""

    title: str
    issuer: str
    date: str
    url: str | None = None

    _check_date = field_validator("date", mode="before")(check_date)


class Skill(Strict):
    """A skill shown on the website's Skills page."""

    id: str
    name: str


class SkillGroup(Strict):
    """A heading on the Skills page and the skills under it."""

    id: str
    name: str
    skills: list[Skill]


class ResumeSkillLine(Strict):
    """One "Label: skills" line in a resume's skills section."""

    label: str
    skills: str


class ResumeSkills(Strict):
    """The resume's skills lines, with optional replacements per variant."""

    default: list[ResumeSkillLine]
    variants: dict[str, list[ResumeSkillLine]] = {}


class SkillsFile(Strict):
    """The contents of content/skills.yaml."""

    groups: list[SkillGroup]
    resume: ResumeSkills


class ProfileWebsite(Strict):
    """Website-only profile text (Markdown)."""

    headline: str
    intro: str
    status: str


class ProfileResume(Strict):
    """Resume-only profile text (Typst markup) and which contact links go in the resume header."""

    summary: str
    header_links: list[Literal["email", "github", "linkedin", "website"]] = ["email", "github", "linkedin"]
    variants: dict[str, ResumeOverride] = {}


class ProfileLinks(Strict):
    """Public profile links."""

    github: str
    linkedin: str
    website: str


class Profile(Strict):
    """The contents of content/profile.yaml. Phone number and street address never go here."""

    name: str
    email: str
    location: str
    links: ProfileLinks
    website: ProfileWebsite
    resume: ProfileResume


class Category(Strict):
    """A project group on the Projects page."""

    id: str
    name: str


class SiteFile(Strict):
    """The contents of content/site.yaml."""

    title: str
    description: str
    url: str
    categories: list[Category]
    featured_count: int = 3
    published_resume: str = "general"


@dataclass
class Project:
    """A project folder: its key, validated project.yaml and the path of its page.md, if any."""

    key: str
    dir: Path
    data: ProjectFile
    page: Path | None

    @property
    def visible(self) -> bool:
        """True when the project appears on the published website."""
        return self.data.website is not None and not self.data.website.hidden


@dataclass
class Experience:
    """A job or degree file and its key."""

    key: str
    data: ExperienceFile


@dataclass
class Content:
    """Everything in content/, validated and cross-checked."""

    root: Path
    site: SiteFile
    profile: Profile
    skills: SkillsFile
    projects: dict[str, Project]
    experience: dict[str, Experience]
    publications: list[Publication]
    certifications: list[Certification]
    pages: dict[str, Path] = field(default_factory=dict)

    def skill_names(self) -> dict[str, str]:
        """Map every website skill id to its display name."""
        return {s.id: s.name for g in self.skills.groups for s in g.skills}


def _read_yaml(path: Path) -> object:
    """Parse a YAML file, turning syntax errors into a ContentError that names the file and line."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"{path}:{mark.line + 1}" if mark else str(path)
        problem = getattr(exc, "problem", None) or str(exc)
        hint = ""
        if "alias" in str(problem) or "anchor" in str(problem):
            hint = " (a value starting with * or & must be wrapped in quotes)"
        raise ContentError(f"{where}: YAML syntax error: {problem}{hint}") from exc


def _split_bullets(data: object, where: str = "") -> list[str]:
    """Find bullets that YAML split at ": " into a key and value because they weren't quoted."""
    found = []
    if isinstance(data, dict):
        for k, v in data.items():
            found += _split_bullets(v, f"{where}.{k}" if where else str(k))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if where.endswith("bullets") and isinstance(item, dict) and "text" not in item and len(item) == 1:
                found.append(f"{where}.{i}")
            else:
                found += _split_bullets(item, f"{where}.{i}")
    return found


def _parse[M: BaseModel](model: type[M], data: object, path: Path) -> M:
    """Validate data against a model, reporting each problem as file: field.path: message."""
    split = _split_bullets(data)
    if split:
        raise ContentError(
            "\n".join(
                f"{path}: {loc}: this bullet contains a colon followed by a space, so YAML read it as "
                "'key: value'. Wrap the whole bullet in single quotes (and double any ' inside it)."
                for loc in split
            )
        )
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(top level)"
            msg = err["msg"]
            if err["type"] == "extra_forbidden":
                msg = "unknown field (misspelt, or in the wrong section?)"
            lines.append(f"{path}: {loc}: {msg}")
        raise ContentError("\n".join(lines)) from exc


def load(root: Path) -> Content:
    """Load content/ under the repository root and cross-check references between files."""
    base = root / "content"
    errors: list[str] = []

    def attempt(fn, *args):
        """Run one loader, collecting its error message instead of stopping at the first problem."""
        try:
            return fn(*args)
        except ContentError as exc:
            errors.append(str(exc))
            return None

    site = attempt(lambda: _parse(SiteFile, _read_yaml(base / "site.yaml"), base / "site.yaml"))
    profile = attempt(lambda: _parse(Profile, _read_yaml(base / "profile.yaml"), base / "profile.yaml"))
    skills = attempt(lambda: _parse(SkillsFile, _read_yaml(base / "skills.yaml"), base / "skills.yaml"))

    def load_list[M: BaseModel](model: type[M], name: str) -> list[M]:
        """Load a YAML file that holds a list of entries of one model."""
        path = base / name
        data = _read_yaml(path)
        if not isinstance(data, list):
            raise ContentError(f"{path}: expected a list of entries")
        out = []
        for i, item in enumerate(data):
            out.append(_parse(model, item, Path(f"{path} (entry {i + 1})")))
        return out

    publications = attempt(load_list, Publication, "publications.yaml") or []
    certifications = attempt(load_list, Certification, "certifications.yaml") or []

    projects: dict[str, Project] = {}
    for folder in sorted(p for p in (base / "projects").iterdir() if p.is_dir()):
        yaml_path = folder / "project.yaml"
        if not yaml_path.exists():
            errors.append(f"{folder}: missing project.yaml")
            continue
        data = attempt(lambda p=yaml_path: _parse(ProjectFile, _read_yaml(p), p))
        if data is None:
            continue
        page = folder / "page.md"
        projects[folder.name] = Project(folder.name, folder, data, page if page.exists() else None)

    experience: dict[str, Experience] = {}
    for path in sorted((base / "experience").glob("*.yaml")):
        data = attempt(lambda p=path: _parse(ExperienceFile, _read_yaml(p), p))
        if data is not None:
            experience[path.stem] = Experience(path.stem, data)

    pages = {p.stem: p for p in sorted((base / "pages").glob("*.md"))}

    if errors or site is None or profile is None or skills is None:
        raise ContentError("\n".join(errors).replace(f"{root}/", ""))

    content = Content(root, site, profile, skills, projects, experience, publications, certifications, pages)
    _cross_check(content)
    return content


def _cross_check(content: Content) -> None:
    """Check references between files: categories, skill ids, featured count and publication links."""
    errors: list[str] = []
    categories = {c.id for c in content.site.categories}
    skill_ids = set(content.skill_names())
    group_ids = [g.id for g in content.skills.groups]
    all_skill_ids = [s.id for g in content.skills.groups for s in g.skills]
    for dup in {i for i in all_skill_ids if all_skill_ids.count(i) > 1}:
        errors.append(f"content/skills.yaml: skill id {dup!r} is used more than once")
    for dup in {i for i in group_ids if group_ids.count(i) > 1}:
        errors.append(f"content/skills.yaml: group id {dup!r} is used more than once")

    def check_skills(where: str, ids: list[str]) -> None:
        """Report unknown skill ids, suggesting the closest known id."""
        for sid in ids:
            if sid not in skill_ids:
                close = _closest(sid, skill_ids)
                hint = f" (did you mean {close!r}?)" if close else ""
                errors.append(f"{where}: skills: unknown skill {sid!r}{hint}")

    for p in content.projects.values():
        where = f"content/projects/{p.key}/project.yaml"
        if p.data.category not in categories:
            errors.append(f"{where}: category: {p.data.category!r} is not defined in content/site.yaml")
        check_skills(where, p.data.skills)
        if p.data.website is None and p.data.resume is None:
            errors.append(f"{where}: needs a website: part, a resume: part, or both")
        if p.data.repository and "/" in p.data.repository:
            errors.append(
                f"{where}: repository: give the repository name only, e.g. {p.data.repository.split('/')[-1]!r}"
            )
    for e in content.experience.values():
        check_skills(f"content/experience/{e.key}.yaml", e.data.skills)
        if e.data.website and e.data.website.project and e.data.website.project not in content.projects:
            errors.append(f"content/experience/{e.key}.yaml: website.project: no project {e.data.website.project!r}")

    featured = [p.key for p in content.projects.values() if p.visible and p.data.website and p.data.website.featured]
    if len(featured) > content.site.featured_count:
        errors.append(
            f"content/site.yaml: featured_count is {content.site.featured_count} but "
            f"{len(featured)} projects are featured: {', '.join(featured)}"
        )
    for pub in content.publications:
        if pub.website.project and pub.website.project not in content.projects:
            errors.append(f"content/publications.yaml: {pub.key}: website.project: no project {pub.website.project!r}")
    if errors:
        raise ContentError("\n".join(sorted(errors)))


def _closest(word: str, options: set[str]) -> str | None:
    """Return the option most similar to word, if any is reasonably close."""
    import difflib

    match = difflib.get_close_matches(word, sorted(options), n=1, cutoff=0.6)
    return match[0] if match else None
