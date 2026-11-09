"""Build the static website from content/ into _site/."""

from __future__ import annotations

import datetime as dt
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from . import markdown
from .content import Content, Project, date_key, format_date

NAV = [
    ("/projects/", "Projects", "projects"),
    ("/experience/", "Experience", "experience"),
    ("/skills/", "Skills", "skills"),
    ("/research/", "Research", "research"),
    ("/contact/", "Contact", "contact"),
    ("/resume.pdf", "Resume", "resume"),
]
STATIC = Path(__file__).parent / "static"


@dataclass
class BuildReport:
    """Problems found while building: errors stop the build, warnings are only printed."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _date_range(start: str, end: str | None) -> str:
    """Format a start and end date for the website, e.g. "Oct 2025 – present"."""

    def short(d: str) -> str:
        """Abbreviate the month name to three letters."""
        text = format_date(d)
        parts = text.split(" ")
        return f"{parts[0][:3]} {parts[1]}" if len(parts) == 2 else text

    if end is None:
        return f"{short(start)} – present"
    if start == end:
        return short(start)
    return f"{short(start)} – {short(end)}"


def _environment() -> Environment:
    """Create the Jinja2 environment with the helper functions the templates use."""
    env = Environment(
        loader=PackageLoader("portfolio", "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.globals.update(
        inline=lambda text: Markup(markdown.render_inline(text)),
        block=lambda text: Markup(markdown.render_block(text)),
        year=lambda d: format_date(d, month=False),
        month=format_date,
        daterange=_date_range,
        venue=lambda v: v.removeprefix("In: "),
    )
    return env


def ordered_projects(content: Content, *, drafts: bool) -> list[tuple[object, list[Project]]]:
    """Projects grouped by category in site.yaml order, newest first; hidden ones only for drafts."""
    groups = []
    for category in content.site.categories:
        items = [
            p
            for p in content.projects.values()
            if p.data.category == category.id and p.data.website and (p.visible or drafts)
        ]
        items.sort(key=lambda p: (date_key(p.data.date), p.data.title), reverse=True)
        if items:
            groups.append((category, items))
    return groups


def _source_url(content: Content, p: Project) -> str | None:
    """The public GitHub URL of a project's repository, or None if it has none or is private."""
    if not p.data.repository or p.data.private:
        return None
    return f"{content.profile.links.github.rstrip('/')}/{p.data.repository}"


def _write(path: Path, text: str) -> None:
    """Write a generated file, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_site(content: Content, out: Path, *, drafts: bool = False) -> BuildReport:
    """Render every page into out/ (which is emptied first) and return the problems found."""
    report = BuildReport()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in STATIC.iterdir():
        shutil.copy2(f, out / f.name)

    env = _environment()
    groups = ordered_projects(content, drafts=drafts)
    listed = [p for _, items in groups for p in items]
    with_pages = [p for p in listed if p.page]
    shown_keys = {p.key for p in listed}
    skill_names = content.skill_names()
    work = sorted(
        (e for e in content.experience.values() if e.data.type == "work"),
        key=lambda e: date_key(e.data.start),
        reverse=True,
    )
    education = sorted(
        (e for e in content.experience.values() if e.data.type == "education"),
        key=lambda e: date_key(e.data.start),
        reverse=True,
    )

    common = {
        "site": content.site,
        "profile": content.profile,
        "nav": NAV,
        "drafts": drafts,
        "updated": format_date(dt.date.today().strftime("%Y-%m")),
    }

    def page(
        template: str, path: str, section: str, title: str, description: str | None = None, **extra: object
    ) -> None:
        """Render one template to the file for a site path such as /projects/."""
        html = env.get_template(template).render(
            **common,
            section=section,
            path=path,
            page_title=title,
            description=description or content.site.description,
            **extra,
        )
        target = out / path.lstrip("/")
        if path.endswith("/"):
            target = target / "index.html"
        _write(target, html)

    name = content.profile.name

    # Home
    featured = [p for p in listed if p.data.website and p.data.website.featured]
    page(
        "home.html",
        "/",
        "home",
        name,
        featured=featured,
        project_count=len(listed),
        work=work,
        publications=content.publications,
    )

    # Projects list and one page per project
    page("projects.html", "/projects/", "projects", f"Projects · {name}", groups=groups)
    categories = {c.id: c for c in content.site.categories}
    for i, p in enumerate(with_pages):
        assert p.page is not None and p.data.website is not None
        body, render_env = markdown.render_page(
            p.page.read_text(encoding="utf-8"), p.page.relative_to(content.root), p.dir
        )
        report.errors += render_env.errors
        report.warnings += render_env.warnings
        for asset in p.dir.rglob("*"):
            if asset.is_file() and asset.name not in {"project.yaml", "page.md"}:
                dest = out / "projects" / p.key / asset.relative_to(p.dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, dest)
        page(
            "project.html",
            f"/projects/{p.key}/",
            "projects",
            f"{p.data.title} · {name}",
            description=p.data.website.summary,
            p=p,
            category=categories[p.data.category],
            source=_source_url(content, p),
            body=Markup(body),
            built_with=[(s, skill_names[s]) for s in p.data.skills],
            prev=with_pages[i - 1] if i > 0 else None,
            next=with_pages[i + 1] if i + 1 < len(with_pages) else None,
        )

    # Experience
    page(
        "experience.html",
        "/experience/",
        "experience",
        f"Experience · {name}",
        work=work,
        education=education,
        certifications=content.certifications,
    )

    # Skills, each linked to the shown projects and the jobs that used it
    evidence: dict[str, list[tuple[str, str]]] = {sid: [] for sid in skill_names}
    for e in work + education:
        for sid in e.data.skills:
            evidence[sid].append((f"/experience/#{e.key}", e.data.organisation.split(" – ")[0]))
    for p in with_pages:
        for sid in p.data.skills:
            evidence[sid].append((f"/projects/{p.key}/", p.data.title.split(":")[0]))
    page("skills.html", "/skills/", "skills", f"Skills · {name}", groups=content.skills.groups, evidence=evidence)

    # Research
    def shown(key: str | None) -> Project | None:
        """The project with this key if it has a page on this build, else None."""
        p = content.projects.get(key) if key else None
        return p if p and p.key in shown_keys and p.page else None

    theses = [(e, shown(e.data.website.project if e.data.website else None)) for e in education if e.data.thesis]
    page(
        "research.html",
        "/research/",
        "research",
        f"Research · {name}",
        publications=[(pub, shown(pub.website.project)) for pub in content.publications],
        theses=theses,
    )

    # Standalone Markdown pages such as contact.md
    for key, path in content.pages.items():
        body, render_env = markdown.render_page(
            path.read_text(encoding="utf-8"), path.relative_to(content.root), path.parent, allow_h1=True
        )
        report.errors += render_env.errors
        report.warnings += render_env.warnings
        page("page.html", f"/{key}/", key, f"{key.replace('-', ' ').capitalize()} · {name}", body=Markup(body))

    page("404.html", "/404.html", "", f"Page not found · {name}")

    urls = ["/", "/projects/", "/experience/", "/skills/", "/research/"] + [f"/{k}/" for k in content.pages]
    urls += [f"/projects/{p.key}/" for p in with_pages if p.visible]
    sitemap = "\n".join(f"  <url><loc>{content.site.url}{u}</loc></url>" for u in urls)
    _write(
        out / "sitemap.xml",
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n',
    )
    _write(out / "robots.txt", f"User-agent: *\nSitemap: {content.site.url}/sitemap.xml\n")
    return report
