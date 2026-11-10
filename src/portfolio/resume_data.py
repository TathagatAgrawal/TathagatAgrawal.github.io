"""Build everything one resume shows, ready for the Typst layout in resume/lib.typ.

The content files hold shared text and per-resume overrides. This module applies the overrides for one
resume (a resume's own text, then the resumes' own, then the shared text), picks and orders its jobs,
projects, papers and skill lines as content/config.yaml says, formats dates, and converts every piece of
Markdown into Typst markup. The result is plain data (strings, lists and dicts) that Typst only has to lay
out, so Typst never has to read or interpret the content files itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from .content import Bullet, Content, ContentError, Experience, Link, NestedBullet, Project, format_date
from .typst_markup import to_typst

GITHUB = "https://github.com/"


class _Convert:
    """Converts Markdown to Typst and reports a failure with the file and field it came from."""

    def __init__(self, where: str) -> None:
        """Remember which file the text being converted came from."""
        self.where = where

    def __call__(self, text: str, field: str) -> str:
        """Convert one Markdown string, naming the field if it contains something Typst can't show."""
        try:
            return to_typst(text)
        except ValueError as exc:
            raise ContentError(f"{self.where}: {field}: {exc}") from exc

    def bullets(self, items: list[Bullet], field: str) -> list[str | dict[str, object]]:
        """Convert a list of bullets; a bullet with sub-bullets becomes {"text": ..., "bullets": [...]}."""
        out: list[str | dict[str, object]] = []
        for i, item in enumerate(items):
            where = f"{field}.{i}"
            if isinstance(item, NestedBullet):
                out.append(
                    {
                        "text": self(item.text, f"{where}.text"),
                        "bullets": [self(sub, f"{where}.bullets.{j}") for j, sub in enumerate(item.bullets)],
                    }
                )
            else:
                out.append(self(item, where))
        return out


def resume_range(start: str, end: str | None) -> str:
    """Format a start and end date as a resume shows it; no end date means the role is current."""
    if end is None:
        return f"{format_date(start)} – Present"
    if start == end:
        return format_date(start)
    return f"{format_date(start)} – {format_date(end)}"


def _github_url(content: Content, repository: str) -> str:
    """The address of one of the user's GitHub repositories."""
    user = content.profile.links.github.split("/")[-1]
    return f"{GITHUB}{user}/{repository}"


@dataclass
class _ResumeProject:
    """A project's text as one resume shows it."""

    title: str
    tech: str | None
    bullets: list[Bullet]
    short: str | None
    link: Link | None


def _project_fields(project: Project, name: str) -> _ResumeProject:
    """A project's resume fields with this resume's own replacements applied over the shared ones."""
    base = project.data.resume
    assert base is not None  # the config check guarantees projects on a resume have a resume: part
    fields = _ResumeProject(base.title or project.data.title, base.tech, base.bullets, base.short, base.link)
    variant = base.variants.get(name)
    if variant:
        fields.title = variant.title or fields.title
        fields.tech = variant.tech if variant.tech is not None else fields.tech
        fields.bullets = variant.bullets if variant.bullets is not None else fields.bullets
        fields.short = variant.short if variant.short is not None else fields.short
        fields.link = variant.link or fields.link
    return fields


def _experience_entry(entry: Experience, name: str, convert: _Convert, *, education: bool) -> dict[str, object]:
    """One job or degree: heading lines on the left and right, then its bullets."""
    e = entry.data
    if education:
        subtitle = f"{e.organisation}, {e.location}" if e.location else e.organisation
        where = e.grade
    else:
        subtitle = e.organisation
        where = e.location
    return {
        "title": e.resume_title(name),
        "subtitle": subtitle,
        "when": resume_range(e.start, e.end),
        "place": where,
        "bullets": convert.bullets(e.resume_bullets(name), "bullets"),
    }


def resume_model(content: Content, name: str) -> dict[str, object]:
    """Everything the resume called name shows, in the order it shows it.

    Raises ContentError if some text can't be shown on a resume (for example an image in a bullet).
    """
    profile = content.profile
    config = content.site.resumes[name]
    layout = {k.replace("_", "-"): v for k, v in config.layout.model_dump().items() if v is not None}

    links: list[dict[str, str]] = []
    for kind in profile.resume.header_links:
        if kind == "email":
            links.append({"text": profile.email})
        else:
            links.append(
                {
                    "text": {"github": "GitHub", "linkedin": "LinkedIn", "website": "Website"}[kind],
                    "url": getattr(profile.links, kind),
                }
            )

    sections: list[dict[str, object]] = []
    for kind in config.sections:
        if kind == "summary":
            variant = profile.resume.variants.get(name)
            text = variant.summary if variant and variant.summary else profile.resume.summary
            sections.append({"kind": kind, "text": _Convert("content/index.md")(text, "resume.summary")})
        elif kind == "skills":
            lines = []
            for ref in config.skills:
                line_id, label = (ref, None) if isinstance(ref, str) else (ref.line, ref.label)
                line = content.skills.resume_lines[line_id]
                lines.append({"label": label or line.label, "skills": line.skills})
            sections.append({"kind": kind, "lines": lines})
        elif kind in {"experience", "education"}:
            entries = []
            for key in getattr(config, kind):
                entry = content.experience[key]
                convert = _Convert(f"content/experience/{key}.yaml")
                entries.append(_experience_entry(entry, name, convert, education=kind == "education"))
            sections.append({"kind": kind, "entries": entries})
        elif kind == "projects":
            sections.append(_projects_section(content, name, config.projects, config.other_projects))
        elif kind == "publications":
            items = []
            for number, key in enumerate(config.publications, 1):
                pub = next(p for p in content.publications if p.key == key)
                convert = _Convert(f"content/research/{key}/index.md")
                items.append(
                    {
                        "number": number,
                        "cite": f"{', '.join(pub.authors)} ({pub.year}) {pub.resume.title or pub.title}. {pub.venue}.",
                        "url": pub.url,
                        "url_label": pub.url_label,
                        "note": convert(pub.resume.note, "resume.note") if pub.resume.note else None,
                    }
                )
            sections.append({"kind": kind, "items": items})
        elif kind == "certifications":
            entries = [
                {"title": c.title, "issuer": c.issuer, "date": format_date(c.date), "url": c.url}
                for c in content.certifications
            ]
            sections.append({"kind": kind, "entries": entries})
    return {"name": profile.name, "links": links, "layout": layout, "variant": name, "sections": sections}


def _projects_section(content: Content, name: str, keys: list[str], other_keys: list[str]) -> dict[str, object]:
    """The Projects section: full entries with bullets, then one-line entries under "Other projects"."""
    entries = []
    for key in keys:
        project = content.projects[key]
        convert = _Convert(f"content/projects/{key}/index.md")
        fields = _project_fields(project, name)
        if project.data.repository and not project.data.private:
            link: dict[str, str] | None = {"text": "GitHub", "url": _github_url(content, project.data.repository)}
        elif fields.link is not None:
            link = {"text": fields.link.label, "url": fields.link.url}
        else:
            link = None
        entries.append(
            {
                "title": fields.title,
                "tech": fields.tech,
                "date": format_date(project.data.date),
                "link": link,
                "bullets": convert.bullets(fields.bullets, "resume.bullets"),
            }
        )
    others = []
    for key in other_keys:
        project = content.projects[key]
        convert = _Convert(f"content/projects/{key}/index.md")
        fields = _project_fields(project, name)
        url = None
        if project.data.repository and not project.data.private:
            url = _github_url(content, project.data.repository)
        details = ", ".join(x for x in (fields.tech, format_date(project.data.date)) if x)
        others.append(
            {
                "title": fields.title,
                "url": url,
                "details": details,
                "short": convert(fields.short, "resume.short") if fields.short else "",
            }
        )
    return {"kind": "projects", "entries": entries, "others": others}
