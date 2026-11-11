"""Load and validate everything in content/ into typed objects.

Projects, papers, theses and the profile are Markdown files: YAML frontmatter between `---` lines, then
an optional Markdown body. Jobs and degrees, skills and certifications are YAML files. All text is
Markdown. The website reads the objects made here as they are; the resumes get their data from
`resume_data`, which applies each resume's overrides and converts the text for Typst.
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
    """A bullet with sub-bullets underneath it."""

    text: str
    bullets: list[str]


Bullet = str | NestedBullet


class ResumeOverride(Strict):
    """Fields replaced for one resume (for example the one-page general resume), written in Markdown."""

    title: str | None = None
    tech: str | None = None
    bullets: list[Bullet] | None = None
    short: str | None = None
    link: Link | None = None
    summary: str | None = None


class ProjectResume(Strict):
    """The resume-only fields of a project, in Markdown, with optional replacements per resume.

    `title` and `link` apply to every resume; `variants.<resume>` replaces any of them for one resume.
    """

    title: str | None = None
    tech: str | None = None
    bullets: list[Bullet] = []
    short: str | None = None
    link: Link | None = None
    variants: dict[str, ResumeOverride] = {}


class ProjectFile(Strict):
    """The frontmatter of content/projects/<key>/index.md; the page itself is the Markdown body."""

    title: str
    date: str
    category: str
    repository: str | None = None
    private: bool = False
    skills: list[str] = []
    links: list[Link] = []
    summary: str
    result: str | None = None
    status: str = "Complete"
    resume: ProjectResume | None = None

    _check_date = field_validator("date", mode="before")(check_date)


class ExperienceWebsite(Strict):
    """Replacements used only on the website: use them when the website should say something different."""

    bullets: list[Bullet] = []


class ExperienceResume(Strict):
    """Replacements used only on resumes, for every resume or (under `variants`) for one."""

    title: str | None = None
    bullets: list[Bullet] | None = None
    variants: dict[str, ResumeOverride] = {}


class ExperienceFile(Strict):
    """The contents of content/experience/<key>.yaml.

    `bullets` are shown on the website and on every resume. `website.bullets` and `resume.bullets` replace
    them on that side only, and `resume.variants.<resume>.bullets` for one resume.
    """

    type: Literal["work", "education"]
    role: str
    organisation: str
    location: str | None = None
    start: str
    end: str | None = None
    grade: str | None = None
    skills: list[str] = []
    summary: str | None = None
    bullets: list[Bullet] = []
    website: ExperienceWebsite | None = None
    resume: ExperienceResume | None = None

    _check_dates = field_validator("start", "end", mode="before")(check_date)

    def site_bullets(self) -> list[Bullet]:
        """The bullets the website shows: its own if given, otherwise the shared ones."""
        return self.website.bullets if self.website and self.website.bullets else self.bullets

    def resume_bullets(self, name: str) -> list[Bullet]:
        """The bullets one resume shows: that resume's own, else the resumes' own, else the shared ones."""
        if self.resume:
            variant = self.resume.variants.get(name)
            if variant and variant.bullets is not None:
                return variant.bullets
            if self.resume.bullets is not None:
                return self.resume.bullets
        return self.bullets

    def resume_title(self, name: str) -> str:
        """The heading one resume shows: that resume's own, else the resumes' own, else the role."""
        if self.resume:
            variant = self.resume.variants.get(name)
            if variant and variant.title:
                return variant.title
            if self.resume.title:
                return self.resume.title
        return self.role


class PublicationResume(Strict):
    """Resume fields of a paper: a shorter title if needed, and a note after the citation (Markdown)."""

    title: str | None = None
    note: str | None = None


class Publication(Strict):
    """The frontmatter of content/research/<key>/index.md; the key is the folder name and the body is the overview."""

    key: str = ""
    body: str = ""  # the Markdown below the frontmatter, filled in by the loader
    authors: list[str]
    year: int
    title: str
    venue: str
    url: str | None = None
    url_label: str = "Paper link"
    summary: str | None = None
    project: str | None = None  # the project page about it
    thesis: str | None = None  # the thesis it came from
    resume: PublicationResume = PublicationResume()

    @property
    def page(self) -> bool:
        """True when the paper has an overview page: some text below the frontmatter."""
        return bool(self.body.strip())


class Thesis(Strict):
    """The frontmatter of a thesis in content/research/<key>/index.md (marked `kind: thesis`).

    `degree` is the key of the education entry in content/experience/ that it was written for, which
    supplies the degree, the university and the year. The key and the body are filled in by the loader.
    """

    kind: Literal["thesis"]
    key: str = ""
    body: str = ""
    title: str
    degree: str
    repository: str | None = None
    private: bool = False
    skills: list[str] = []
    links: list[Link] = []
    summary: str

    @property
    def page(self) -> bool:
        """True when the thesis has a page: some text below the frontmatter."""
        return bool(self.body.strip())


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
    """One "Label: skills" line of a resume's Technical Skills section, in plain text."""

    label: str
    skills: str


class SkillsFile(Strict):
    """The contents of content/skills.yaml: the website's skill groups and the resume's skill lines.

    Each resume line is written once, under an id; the resumes in content/config.yaml pick and order them.
    """

    groups: list[SkillGroup]
    resume_lines: dict[str, ResumeSkillLine]


class ProfileResume(Strict):
    """Resume-only profile text (Markdown) and which contact links go in the resume header."""

    summary: str
    header_links: list[Literal["email", "github", "linkedin", "website"]] = ["email", "github", "linkedin"]
    variants: dict[str, ResumeOverride] = {}


class ProfileLinks(Strict):
    """Public profile links."""

    github: str
    linkedin: str
    website: str


class Profile(Strict):
    """The frontmatter of content/index.md. Phone number and street address never go here."""

    name: str
    email: str
    location: str
    links: ProfileLinks
    headline: str  # the large line at the top of the home page
    intro: str = ""  # filled in from the Markdown body of content/index.md
    status: str  # Markdown: current role and availability
    resume: ProfileResume


class Category(Strict):
    """A project group on the Projects page."""

    id: str
    name: str


Section = Literal["summary", "skills", "experience", "projects", "publications", "education", "certifications"]
LENGTH = re.compile(r"^\d+(\.\d+)?(pt|in|mm|cm|em)$")
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
# The color names Typst has built in.
COLOR_NAMES = [
    "black",
    "gray",
    "silver",
    "white",
    "navy",
    "blue",
    "aqua",
    "teal",
    "eastern",
    "purple",
    "fuchsia",
    "maroon",
    "red",
    "orange",
    "yellow",
    "olive",
    "green",
    "lime",
]


class ResumeLayout(Strict):
    """Optional layout overrides for one resume.

    The sizes are Typst lengths such as 0.4in, 16pt or 0.45em. `font` is a font family, or a list of them to
    try in order; it must be one of the fonts bundled with the build or one whose files are in resume/fonts/.
    `accent` is the theme color: a hex color such as "#0b5cad" (in quotes, since # starts a comment in YAML) or a
    Typst color name such as navy. It colors your name, the section headings and their rules, and the links.
    """

    margin: str | None = None
    gap: str | None = None
    name_size: str | None = None
    heading_size: str | None = None
    font_size: str | None = None
    font: list[str] | None = None
    accent: str | None = None

    @field_validator("margin", "gap", "name_size", "heading_size", "font_size", mode="before")
    @classmethod
    def _check_length(cls, value: object) -> object:
        """Require a number with a unit, which is what Typst needs."""
        if value is not None and not LENGTH.match(str(value)):
            raise ValueError(f"expected a length with a unit such as 0.4in, 16pt or 0.45em, got {value!r}")
        return str(value) if value is not None else None

    @field_validator("accent", mode="before")
    @classmethod
    def _check_accent(cls, value: object) -> object:
        """Accept a hex color or a Typst color name, and nothing else (the value is evaluated as Typst)."""
        if value is None:
            return None
        text = str(value).strip()
        if not (HEX_COLOR.match(text) or text in COLOR_NAMES):
            raise ValueError(
                f'expected a hex color in quotes such as "#0b5cad", or one of {", ".join(COLOR_NAMES)}; got {value!r}'
            )
        return text

    @field_validator("font", mode="before")
    @classmethod
    def _check_font(cls, value: object) -> object:
        """Accept one family name or a list of them, and reject empty names."""
        if value is None:
            return None
        names = [value] if isinstance(value, str) else value
        if not isinstance(names, list) or not names or not all(isinstance(n, str) and n.strip() for n in names):
            raise ValueError("expected a font family name such as New Computer Modern, or a list of them")
        return [n.strip() for n in names]


class SkillLineRef(Strict):
    """A resume skill line picked by id, with a different label for this resume."""

    line: str
    label: str | None = None


class ResumeConfig(Strict):
    """One resume: its sections in order, and the keys of the jobs, projects and papers under them."""

    filename: str | None = None  # the name of its PDF outside the repository, without .pdf
    sections: list[Section]
    skills: list[str | SkillLineRef] = []  # ids of the lines in content/skills.yaml, in order
    experience: list[str] = []
    education: list[str] = []
    projects: list[str] = []
    other_projects: list[str] = []
    publications: list[str] = []
    layout: ResumeLayout = ResumeLayout()

    @field_validator("filename")
    @classmethod
    def _check_filename(cls, value: str | None) -> str | None:
        """Reject names that are not a plain file name (no folders, no characters a file system refuses)."""
        if value is not None and (
            not value.strip() or value.startswith(".") or re.search(r'[/\\:*?"<>|\x00-\x1f]', value)
        ):
            raise ValueError('a file name without folders, a leading dot or any of / \\ : * ? " < > |')
        return value


class WebsiteConfig(Strict):
    """What the website shows: its projects, the featured ones in order, and the resume it publishes."""

    projects: list[str]
    featured: list[str] = []
    resume: str


class SiteFile(Strict):
    """The contents of content/config.yaml: the one file that decides what appears on the website and resumes."""

    title: str
    description: str
    url: str
    home_title: str
    descriptions: dict[str, str] = {}
    categories: list[Category]
    website: WebsiteConfig
    resumes: dict[str, ResumeConfig]


@dataclass
class Project:
    """A project folder: its key, the validated frontmatter of index.md and that file's Markdown body."""

    key: str
    dir: Path
    data: ProjectFile
    path: Path
    body: str
    visible: bool = False  # listed under website.projects in content/config.yaml

    @property
    def page(self) -> bool:
        """True when the project has a web page: some text below the frontmatter."""
        return bool(self.body.strip())


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
    theses: list[Thesis] = field(default_factory=list)

    def skill_names(self) -> dict[str, str]:
        """Map every website skill id to its display name."""
        return {s.id: s.name for g in self.skills.groups for s in g.skills}


def _read_yaml(path: Path) -> object:
    """Parse a YAML file, turning syntax errors into a ContentError that names the file and line."""
    return _parse_yaml(path.read_text(encoding="utf-8"), path)


def _parse_yaml(text: str, path: Path, line_offset: int = 0) -> object:
    """Parse YAML text; line_offset is the number of lines above it in the file, so errors name the right line."""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"{path}:{mark.line + 1 + line_offset}" if mark else str(path)
        problem = getattr(exc, "problem", None) or str(exc)
        hint = ""
        if "alias" in str(problem) or "anchor" in str(problem):
            hint = " (a value starting with * or & must be wrapped in quotes)"
        raise ContentError(f"{where}: YAML syntax error: {problem}{hint}") from exc


def split_entry(text: str, path: Path) -> tuple[object, str]:
    """Split a Markdown file into its parsed YAML frontmatter and its body.

    The file starts with a `---` line; the frontmatter ends at the next line that is only `---`. The
    body is padded with blank lines to the frontmatter's height, so that a line number reported while
    rendering it is the line number in the file.
    """
    if not text.startswith("---\n"):
        raise ContentError(f"{path}:1: expected the file to start with a --- line and YAML frontmatter")
    end = text.find("\n---\n", 3)
    if end == -1 and text.endswith("\n---"):
        end = len(text) - 4
    if end == -1:
        raise ContentError(f"{path}: the frontmatter is never closed; add a line containing only ---")
    front = text[4:end]
    body = text[end + 5 :]
    data = _parse_yaml(front, path, line_offset=1)
    if data is None:
        data = {}  # an empty frontmatter reports the missing fields instead of being skipped
    return data, "\n" * (text[: end + 5].count("\n")) + body


def _read_entry(path: Path) -> tuple[object, str]:
    """Read a Markdown file and split it into frontmatter data and body."""
    return split_entry(path.read_text(encoding="utf-8"), path)


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

    site = attempt(lambda: _parse(SiteFile, _read_yaml(base / "config.yaml"), base / "config.yaml"))
    shown = set(site.website.projects) if site else set()
    skills = attempt(lambda: _parse(SkillsFile, _read_yaml(base / "skills.yaml"), base / "skills.yaml"))

    def load_profile() -> Profile:
        """Load content/index.md: the frontmatter is the profile and the body is the home-page intro."""
        path = base / "index.md"
        data, body = _read_entry(path)
        if isinstance(data, dict) and body.strip():
            data["intro"] = body.strip()
        return _parse(Profile, data, path)

    profile = attempt(load_profile)

    def load_certifications() -> list[Certification]:
        """Load the list in certifications.yaml."""
        path = base / "certifications.yaml"
        data = _read_yaml(path)
        if not isinstance(data, list):
            raise ContentError(f"{path}: expected a list of entries")
        return [_parse(Certification, item, Path(f"{path} (entry {i + 1})")) for i, item in enumerate(data)]

    certifications = attempt(load_certifications) or []

    publications: list[Publication] = []
    theses: list[Thesis] = []
    for path in sorted((base / "research").glob("*/index.md")):
        entry = attempt(lambda p=path: _read_entry(p))
        if entry is None:
            continue
        data = entry[0]
        if isinstance(data, dict):
            data["key"] = path.parent.name
            data["body"] = entry[1]
        if isinstance(data, dict) and "kind" in data:
            thesis = attempt(lambda p=path, d=data: _parse(Thesis, d, p))
            if thesis is not None:
                theses.append(thesis)
            continue
        pub = attempt(lambda p=path, d=data: _parse(Publication, d, p))
        if pub is not None:
            publications.append(pub)
    # Newest first; papers from the same year in alphabetical order of their file names.
    publications.sort(key=lambda pub: (-pub.year, pub.key))

    projects: dict[str, Project] = {}
    for folder in sorted(p for p in (base / "projects").iterdir() if p.is_dir()):
        md_path = folder / "index.md"
        if not md_path.exists():
            errors.append(f"{folder}: missing index.md")
            continue
        entry = attempt(lambda p=md_path: _read_entry(p))
        if entry is None:
            continue
        data = attempt(lambda p=md_path, e=entry: _parse(ProjectFile, e[0], p))
        if data is not None:
            projects[folder.name] = Project(folder.name, folder, data, md_path, entry[1], folder.name in shown)

    experience: dict[str, Experience] = {}
    for path in sorted((base / "experience").glob("*.yaml")):
        data = attempt(lambda p=path: _parse(ExperienceFile, _read_yaml(p), p))
        if data is not None:
            experience[path.stem] = Experience(path.stem, data)

    pages = {p.stem: p for p in sorted((base / "pages").glob("*.md"))}

    if errors or site is None or profile is None or skills is None:
        raise ContentError("\n".join(errors).replace(f"{root}/", ""))

    content = Content(root, site, profile, skills, projects, experience, publications, certifications, pages, theses)
    _cross_check(content)
    return content


def _cross_check(content: Content) -> None:
    """Check references between files: categories, skill ids, publication links and content/config.yaml."""
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
        where = f"content/projects/{p.key}/index.md"
        if p.data.category not in categories:
            errors.append(f"{where}: category: {p.data.category!r} is not defined in content/config.yaml")
        check_skills(where, p.data.skills)
        if p.data.repository and "/" in p.data.repository:
            errors.append(
                f"{where}: repository: give the repository name only, e.g. {p.data.repository.split('/')[-1]!r}"
            )
    for e in content.experience.values():
        check_skills(f"content/experience/{e.key}.yaml", e.data.skills)

    _check_config(content, errors)
    degrees_by_key = {k: e for k, e in content.experience.items() if e.data.type == "education"}
    thesis_keys = {t.key for t in content.theses}
    for t in content.theses:
        where = f"content/research/{t.key}/index.md"
        check_skills(where, t.skills)
        if t.degree not in degrees_by_key:
            close = _closest(t.degree, set(degrees_by_key))
            hint = f" (did you mean {close!r}?)" if close else ""
            errors.append(f"{where}: degree: no education entry {t.degree!r} in content/experience/{hint}")
        if t.repository and "/" in t.repository:
            errors.append(f"{where}: repository: give the repository name only, e.g. {t.repository.split('/')[-1]!r}")
    for pub in content.publications:
        if pub.thesis and pub.thesis not in thesis_keys:
            errors.append(f"content/research/{pub.key}/index.md: thesis: no thesis {pub.thesis!r}")
        if pub.project and pub.project not in content.projects:
            errors.append(f"content/research/{pub.key}/index.md: project: no project {pub.project!r}")
    if errors:
        raise ContentError("\n".join(sorted(errors)))


def _check_config(content: Content, errors: list[str]) -> None:
    """Check that content/config.yaml names real projects, jobs and papers, and that each resume is consistent."""
    where = "content/config.yaml"
    cfg = content.site
    publications = {pub.key for pub in content.publications}

    def check_keys(label: str, keys: list[str], known: set[str], kind: str) -> None:
        """Report keys that name nothing (suggesting the closest one) and keys listed twice."""
        for key in keys:
            if key not in known:
                close = _closest(key, known)
                hint = f" (did you mean {close!r}?)" if close else ""
                errors.append(f"{where}: {label}: no {kind} {key!r}{hint}")
        for dup in sorted({k for k in keys if keys.count(k) > 1}):
            errors.append(f"{where}: {label}: {dup!r} is listed more than once")

    known_pages = {"projects", "experience", "skills", "research", *content.pages}
    for key in cfg.descriptions:
        if key not in known_pages:
            close = _closest(key, known_pages)
            hint = f" (did you mean {close!r}?)" if close else ""
            errors.append(f"{where}: descriptions: {key!r} is not a page{hint}")
    web = cfg.website
    check_keys("website.projects", web.projects, set(content.projects), "project")
    check_keys("website.featured", web.featured, set(web.projects), "project in website.projects")
    if web.resume not in cfg.resumes:
        errors.append(f"{where}: website.resume: no resume {web.resume!r} under resumes:")

    has_resume = {k for k, p in content.projects.items() if p.data.resume is not None}
    jobs = {k for k, e in content.experience.items() if e.data.type == "work"}
    degrees = {k for k, e in content.experience.items() if e.data.type == "education"}
    skill_lines = set(content.skills.resume_lines)
    for name, r in cfg.resumes.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            errors.append(f"{where}: resumes.{name}: use lowercase letters, digits, - and _ in a resume's name")
        label = f"resumes.{name}"
        check_keys(f"{label}.projects", r.projects, has_resume, "project with a resume: part")
        check_keys(f"{label}.other_projects", r.other_projects, has_resume, "project with a resume: part")
        check_keys(f"{label}.experience", r.experience, jobs, "job")
        check_keys(f"{label}.education", r.education, degrees, "degree")
        line_ids = [x if isinstance(x, str) else x.line for x in r.skills]
        check_keys(f"{label}.skills", line_ids, skill_lines, "skill line in content/skills.yaml")
        check_keys(f"{label}.publications", r.publications, publications, "paper")
        check_keys(f"{label}.sections", list(r.sections), set(Section.__args__), "section")
        for section, keys in [
            ("skills", line_ids),
            ("experience", r.experience),
            ("education", r.education),
            ("projects", r.projects),
            ("publications", r.publications),
        ]:
            if section in r.sections and not keys:
                errors.append(f"{where}: {label}: has a {section!r} section but {section}: is empty")
            if keys and section not in r.sections:
                errors.append(f"{where}: {label}: lists {section}: but has no {section!r} section in sections:")
        if r.other_projects and "projects" not in r.sections:
            errors.append(f"{where}: {label}: lists other_projects: but has no 'projects' section in sections:")

    def check_variants(file: str, variants: dict[str, object]) -> None:
        """Report variant names that are not a resume in config.yaml, which would never be used."""
        for variant in variants:
            if variant not in cfg.resumes:
                close = _closest(variant, set(cfg.resumes))
                hint = f" (did you mean {close!r}?)" if close else ""
                errors.append(f"{file}: resume.variants: {variant!r} is not a resume in {where}{hint}")

    for key, p in content.projects.items():
        if p.data.resume:
            check_variants(f"content/projects/{key}/index.md", p.data.resume.variants)
    for key, e in content.experience.items():
        if e.data.resume:
            check_variants(f"content/experience/{key}.yaml", e.data.resume.variants)
    check_variants("content/index.md", content.profile.resume.variants)


def _closest(word: str, options: set[str]) -> str | None:
    """Return the option most similar to word, if any is reasonably close."""
    import difflib

    match = difflib.get_close_matches(word, sorted(options), n=1, cutoff=0.6)
    return match[0] if match else None
